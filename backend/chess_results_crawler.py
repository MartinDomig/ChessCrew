import requests
import pandas as pd
import re
import os
import time
import logging
import hashlib
import tempfile
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse, parse_qs
from bs4 import BeautifulSoup
from db.models import db, Tournament, TournamentPlayer, Player
from sqlalchemy import func
from tournament_importer import import_tournament_from_excel

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChessResultsCrawler:
    def __init__(self):
        self.session = requests.Session()
        self.base_url = "https://chess-results.com"
        self.login_url = f"{self.base_url}/Login.aspx?xx=0"
        self.fed_url = f"{self.base_url}/fed.aspx?lan=0&fed=AUT"
        self.username = "142838"
        self.password = "zbLiZm58Y"
        self.logged_in = False
        
        # Headers to mimic a real browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        
        # Handle SSL and redirects properly
        self.session.verify = True
        self.session.max_redirects = 10

    def login(self):
        """Login to chess-results.com"""
        try:
            # Get the login page first
            response = self.session.get(self.login_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find the login form - usually the main form on the page
            login_form = soup.find('form', {'method': 'post'}) or soup.find('form')
            if not login_form:
                logger.error("Could not find login form")
                return False
            
            # Extract all form data to maintain state (exactly like debug script)
            form_data = {}
            for input_field in login_form.find_all('input'):
                name = input_field.get('name')
                value = input_field.get('value', '')
                input_type = input_field.get('type', '').lower()
                if name and input_type != 'submit':  # Don't include submit buttons yet
                    form_data[name] = value
            
            # Look for viewstate and other ASP.NET specific fields
            for input_field in login_form.find_all('input', {'type': 'hidden'}):
                name = input_field.get('name')
                value = input_field.get('value', '')
                if name:
                    form_data[name] = value
            
            # Set credentials - chess-results.com uses "PNo." and password
            # Try to find the exact field names
            pno_field = None
            password_field = None
            
            for input_field in login_form.find_all('input'):
                name = input_field.get('name', '')
                input_type = input_field.get('type', '').lower()
                
                # Look for user field (Personal Number)
                if 'user' in name.lower() and input_type == 'text':
                    pno_field = name
                elif input_type == 'password':
                    password_field = name
            
            # Set our credentials
            if pno_field:
                form_data[pno_field] = self.username
            if password_field:
                form_data[password_field] = self.password
            
            # Handle submit buttons - only include the login button (exactly like debug script)
            login_button_name = None
            for input_field in login_form.find_all('input'):
                name = input_field.get('name', '')
                input_type = input_field.get('type', '').lower()
                value = input_field.get('value', '').lower()
                
                if input_type == 'submit':
                    if 'login' in value or 'anmelden' in name.lower():
                        login_button_name = name
                        form_data[name] = input_field.get('value', 'Login')
                        break
            
            # Handle cookie checkbox to maintain login session
            for input_field in login_form.find_all('input'):
                name = input_field.get('name', '')
                input_type = input_field.get('type', '').lower()
                
                if input_type == 'checkbox' and 'cookie' in name.lower():
                    form_data[name] = 'on'  # Check the cookie checkbox
                    logger.info(f"Set cookie checkbox: {name}")
            
            logger.info(f"Attempting login with PNo={self.username}, using login button: {login_button_name}")
            logger.debug(f"Form fields being submitted: {list(form_data.keys())}")
            logger.debug(f"Complete form data: {form_data}")
            
            # Submit login form - use the exact same approach as debug script
            login_response = self.session.post(self.login_url, data=form_data, allow_redirects=True)
            login_response.raise_for_status()
            
            # Check if login was successful by looking for logout link or user info
            response_text = login_response.text.lower()
            
            # More comprehensive login success detection
            success_indicators = ["logout", "abmelden", "logged on:", "angemeldet"]
            failure_indicators = ["error", "invalid", "incorrect", "wrong"]
            
            has_success = any(indicator in response_text for indicator in success_indicators)
            has_failure = any(indicator in response_text for indicator in failure_indicators)
            
            # Check if we were redirected away from login page
            is_still_on_login = "login.aspx" in login_response.url.lower()
            
            # Check if we're on the main page (successful redirect)
            is_on_main_page = "default.aspx" in login_response.url.lower() or login_response.url.endswith(".com/")
            
            logger.debug(f"Login analysis - URL: {login_response.url}")
            logger.debug(f"Has success indicators: {has_success}")
            logger.debug(f"Has failure indicators: {has_failure}")
            logger.debug(f"Still on login page: {is_still_on_login}")
            logger.debug(f"On main page: {is_on_main_page}")
            
            if is_on_main_page or (has_success and not is_still_on_login):
                self.logged_in = True
                logger.info("Successfully logged in to chess-results.com")
                return True
            elif is_still_on_login:
                logger.error("Login failed - still on login page, likely invalid credentials")
                logger.debug(f"Response URL: {login_response.url}")
                logger.debug(f"Response content preview: {login_response.text[:500]}")
                return False
            elif has_success and not has_failure:
                logger.info("Login appears successful based on content analysis")
                self.logged_in = True
                return True
            else:
                logger.error("Login failed - no clear success indicators")
                logger.debug(f"Response URL: {login_response.url}")
                return False
                
        except Exception as e:
            logger.error(f"Error during login: {str(e)}")
            return False

    def get_finished_tournaments(self):
        """Get list of finished tournaments from the last 7 days"""
        try:
            if not self.logged_in and not self.login():
                logger.error("Cannot proceed without login")
                return []
            
            # First, get the federation page
            response = self.session.get(self.fed_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for the tournament selection dropdown ("Turnierauswahl")
            # Find the form that contains the dropdown
            dropdown_form = None
            tournament_dropdown = None
            
            # Look for select elements that might contain tournament options
            select_elements = soup.find_all('select')
            
            for select in select_elements:
                options = select.find_all('option')
                for option in options:
                    option_text = option.get_text(strip=True).lower()
                    # Look for "In den letzten 7 tagen beendete turniere" or similar
                    if 'letzten' in option_text and 'beendete' in option_text:
                        tournament_dropdown = select
                        dropdown_form = select.find_parent('form')
                        target_option = option
                        logger.info(f"Found finished tournaments option: {option.get_text(strip=True)}")
                        break
                
                if tournament_dropdown:
                    break
            
            if not tournament_dropdown:
                logger.error("Could not find tournament selection dropdown")
                return []
            
            if not dropdown_form:
                logger.error("Could not find form containing dropdown")
                return []
            
            # Prepare form data for dropdown selection
            form_data = {}
            
            # Get all form inputs to maintain state
            for input_field in dropdown_form.find_all('input'):
                name = input_field.get('name')
                value = input_field.get('value', '')
                if name:
                    form_data[name] = value
            
            # Set the dropdown value to select finished tournaments
            dropdown_name = tournament_dropdown.get('name')
            target_value = target_option.get('value')
            
            if dropdown_name and target_value:
                form_data[dropdown_name] = target_value
                logger.info(f"Setting dropdown {dropdown_name} = {target_value}")
            
            # Submit the form to get finished tournaments
            form_action = dropdown_form.get('action') or self.fed_url
            if not form_action.startswith('http'):
                form_action = urljoin(self.base_url, form_action)
            
            logger.info(f"Submitting dropdown form to: {form_action}")
            dropdown_response = self.session.post(form_action, data=form_data)
            dropdown_response.raise_for_status()
            
            # Parse the response to get tournament links
            soup = BeautifulSoup(dropdown_response.content, 'html.parser')
            
            # Save filtered page for debugging
            try:
                with open('/tmp/filtered_tournaments.html', 'w', encoding='utf-8') as f:
                    f.write(dropdown_response.text)
                logger.debug("Saved filtered page to /tmp/filtered_tournaments.html")
            except:
                pass
            
            # Now look for tournament links in the filtered results
            finished_tournaments = []
            
            # Find all tournament links - try multiple patterns
            tournament_links = soup.find_all('a', href=re.compile(r'tnr.*\.aspx'))
            logger.debug(f"Found {len(tournament_links)} links with 'tnr' pattern")
            
            if not tournament_links:
                # Try alternative patterns
                tournament_links = soup.find_all('a', href=re.compile(r'tnr'))
                logger.debug(f"Found {len(tournament_links)} links with broader 'tnr' pattern")
            
            for link in tournament_links:
                href = link.get('href')
                tournament_name = link.get_text(strip=True)
                
                logger.debug(f"Processing link: '{tournament_name}' -> {href}")
                
                if href and tournament_name:
                    # Filter out navigation links and very short names
                    if len(tournament_name) > 5:  # Reduced from 10 to catch more tournaments
                        full_url = urljoin(self.base_url, href)
                        tournament_id = self.extract_tournament_id(href)
                        
                        if tournament_id:
                            finished_tournaments.append({
                                'name': tournament_name,
                                'url': full_url,
                                'id': tournament_id
                            })
                            logger.debug(f"Added tournament: {tournament_name} (ID: {tournament_id})")
                        else:
                            logger.debug(f"Could not extract ID from: {href}")
                    else:
                        logger.debug(f"Skipped short name: '{tournament_name}'")
                else:
                    logger.debug(f"Skipped link with missing href or name")
            
            logger.info(f"Found {len(finished_tournaments)} finished tournaments")
            return finished_tournaments
            
        except Exception as e:
            logger.error(f"Error getting finished tournaments: {str(e)}")
            return []

    def extract_tournament_id(self, href):
        """Extract tournament ID from URL"""
        try:
            # Pattern: tnr1133378.aspx or tnr1133378.aspx?lan=0
            match = re.search(r'tnr(\d+)', href)
            if match:
                return match.group(1)
            
            # Fallback: look for any number in the URL
            parsed = urlparse(href)
            query_params = parse_qs(parsed.query)
            
            # Check for tnr parameter
            tnr_param = query_params.get('tnr', [None])[0]
            if tnr_param:
                return tnr_param
                
            logger.debug(f"Could not extract tournament ID from: {href}")
            return None
        except Exception as e:
            logger.debug(f"Error extracting tournament ID from {href}: {e}")
            return None

    def get_tournament_details(self, tournament_url, tournament_id):
        """Get tournament details and check if it should be processed"""
        try:
            response = self.session.get(tournament_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Step 1: Check if we need to submit the "Show tournament details" form (anti-crawling measure)
            details_button = soup.find('input', {'name': 'cb_alleDetails', 'type': 'submit'})
            if details_button:
                logger.info(f"Found 'Show tournament details' button for tournament {tournament_id}, submitting form...")
                
                # Get form data for submission
                form = details_button.find_parent('form')
                if form:
                    form_data = {}
                    
                    # Get all hidden inputs
                    for hidden_input in form.find_all('input', type='hidden'):
                        name = hidden_input.get('name')
                        value = hidden_input.get('value', '')
                        if name:
                            form_data[name] = value
                    
                    # Add the button click
                    form_data['cb_alleDetails'] = details_button.get('value', 'Show tournament details')
                    
                    # Submit the form
                    response = self.session.post(tournament_url, data=form_data)
                    response.raise_for_status()
                    soup = BeautifulSoup(response.content, 'html.parser')
                    logger.info(f"Successfully submitted tournament details form for {tournament_id}")
            
            # Step 2: After clicking "Show tournament details", look for tournament content directly on this page
            # Look for final ranking crosstable link or Excel export directly
            final_table_link = None
            crosstable_patterns = [
                r'final.*ranking.*crosstable',
                r'crosstable.*final',
                r'endtabelle.*runden',
                r'kreuztabelle',
                r'final.*table',
                r'end.*table',
                r'tabelle',
                r'table'
            ]
            
            # Try to find crosstable link
            logger.info(f"Looking for tournament table links on page for tournament {tournament_id}")
            all_links = soup.find_all('a', href=True)
            
            for pattern in crosstable_patterns:
                final_table_link = soup.find('a', string=re.compile(pattern, re.IGNORECASE))
                if final_table_link:
                    logger.info(f"Found final ranking crosstable link using pattern: {pattern}")
                    break
            
            # If no specific crosstable link found, look for any tournament-related links
            if not final_table_link:
                for link in all_links:
                    href = link.get('href', '')
                    text = link.get_text().strip()
                    
                    # Look for links that contain the tournament ID and table-related terms
                    if (f'tnr{tournament_id}' in href or tournament_id in href) and \
                       any(term in href.lower() or term in text.lower() 
                           for term in ['table', 'tabelle', 'ranking', 'result', 'ergebnis']):
                        final_table_link = link
                        logger.info(f"Found tournament table link: {text} -> {href}")
                        break
            
            # If still no table link, look for Excel export directly
            if not final_table_link:
                for link in all_links:
                    href = link.get('href', '')
                    text = link.get_text().strip()
                    
                    # Look for Excel export links
                    if 'excel' in href.lower() or 'excel' in text.lower():
                        logger.info(f"Found direct Excel export link: {text} -> {href}")
                        excel_url = href if href.startswith('http') else urljoin(self.base_url, href)
                        
                        return {
                            'excel_url': excel_url,
                            'tournament_id': tournament_id,
                            'name': f'Tournament {tournament_id}',
                            'has_elo_calculation': False  # We'll check this after getting to the table page
                        }
            
            # Step 3: If we found a crosstable link, follow it
            if final_table_link:
                final_table_href = final_table_link.get('href')
                
                # Handle both relative and absolute URLs
                if final_table_href.startswith('http'):
                    final_table_url = final_table_href
                else:
                    final_table_url = urljoin(self.base_url, final_table_href)
                
                logger.info(f"Following final ranking crosstable link: {final_table_url}")
                
                # Navigate to final table page
                response = self.session.get(final_table_url)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Step 4: Check for "Show tournament details" button one more time
                details_button = soup.find('input', {'name': 'cb_alleDetails', 'type': 'submit'}) or \
                                soup.find('input', {'value': re.compile(r'Show tournament details', re.IGNORECASE)})
                if details_button:
                    logger.info(f"Found 'Show tournament details' button on final table page for tournament {tournament_id}, submitting form...")
                    
                    # Get form data for submission
                    form = details_button.find_parent('form')
                    if form:
                        # Get form action
                        action = form.get('action', '')
                        if not action.startswith('http'):
                            action = urljoin(final_table_url, action)
                        
                        form_data = {}
                        
                        # Get all hidden inputs
                        for hidden_input in form.find_all('input', type='hidden'):
                            name = hidden_input.get('name')
                            value = hidden_input.get('value', '')
                            if name:
                                form_data[name] = value
                        
                        # Add the button click
                        button_name = details_button.get('name', 'cb_alleDetails')
                        button_value = details_button.get('value', 'Show tournament details')
                        form_data[button_name] = button_value
                        
                        # Submit the form
                        response = self.session.post(action, data=form_data)
                        response.raise_for_status()
                        soup = BeautifulSoup(response.content, 'html.parser')
                        logger.info(f"Successfully submitted tournament details form on final table page for {tournament_id}")
                        final_table_url = response.url  # Update URL in case of redirect
                
                # Now check for ELO calculation on the table page
                elo_section = soup.find(string=re.compile(r'Elorechnung|Rating calculation', re.IGNORECASE))
                has_elo_calculation = False
                if elo_section:
                    # Find the parent element and check if it contains "-" (indicating no calculation)
                    parent = elo_section.parent
                    if parent:
                        parent_text = parent.get_text().strip()
                        logger.info(f"Found ELO section for tournament {tournament_id}: {parent_text}")
                        # If it contains "-" or "no" or "nein", there's no ELO calculation
                        if not any(indicator in parent_text.lower() for indicator in ['-', 'no', 'nein', 'none']):
                            has_elo_calculation = True
                            logger.info(f"Tournament {tournament_id} has ELO calculation")
                        else:
                            logger.info(f"Tournament {tournament_id} has no ELO calculation (found: {parent_text})")
                else:
                    logger.info(f"No ELO section found for tournament {tournament_id}, assuming no ELO calculation")
                
                # Extract tournament name from the page
                tournament_name = None
                title_elements = soup.find_all(['h1', 'h2', 'title'])
                for elem in title_elements:
                    text = elem.get_text().strip()
                    if text and 'chess-results' not in text.lower():
                        tournament_name = text
                        break
                
                return {
                    'final_table_url': final_table_url,
                    'tournament_id': tournament_id,
                    'name': tournament_name or f'Tournament {tournament_id}',
                    'url': final_table_url,
                    'has_elo_calculation': has_elo_calculation
                }
            
            # If no table links found, try to construct URLs manually
            logger.info(f"No table links found, trying to construct URLs for tournament {tournament_id}")
            
            # Try common URL patterns for chess-results.com
            base_tournament_url = f"https://chess-results.com/tnr{tournament_id}.aspx"
            table_url_patterns = [
                f"{base_tournament_url}?lan=1&art=4&turdet=YES",  # Final ranking with details
                f"{base_tournament_url}?lan=1&art=1&turdet=YES",  # Starting list with details
                f"{base_tournament_url}?lan=1&art=2&turdet=YES"   # Pairings with details
            ]
            
            for pattern_url in table_url_patterns:
                try:
                    logger.info(f"Trying constructed URL: {pattern_url}")
                    response = self.session.get(pattern_url)
                    response.raise_for_status()
                    
                    # Check if this page has tournament data (look for player tables)
                    soup_test = BeautifulSoup(response.content, 'html.parser')
                    if soup_test.find('table') or soup_test.find(string=re.compile(r'Rang|Rank|Name', re.IGNORECASE)):
                        logger.info(f"Found tournament data at constructed URL: {pattern_url}")
                        
                        # Check for ELO calculation on this page
                        elo_section = soup_test.find(string=re.compile(r'Elorechnung|Rating calculation', re.IGNORECASE))
                        has_elo_calculation = False
                        if elo_section:
                            parent = elo_section.parent
                            if parent:
                                parent_text = parent.get_text().strip()
                                logger.info(f"Found ELO section for tournament {tournament_id}: {parent_text}")
                                if not any(indicator in parent_text.lower() for indicator in ['-', 'no', 'nein', 'none']):
                                    has_elo_calculation = True
                                    logger.info(f"Tournament {tournament_id} has ELO calculation")
                        
                        return {
                            'final_table_url': pattern_url,
                            'tournament_id': tournament_id,
                            'name': f'Tournament {tournament_id}',
                            'url': pattern_url,
                            'has_elo_calculation': has_elo_calculation
                        }
                except Exception as e:
                    logger.info(f"Constructed URL failed: {pattern_url} - {e}")
                    continue
            
            # Fallback: look for Excel export link directly on the current page
            excel_export_link = soup.find('a', string=re.compile(r'Export to Excel', re.IGNORECASE))
            if excel_export_link:
                excel_url = excel_export_link.get('href')
                # Handle both relative and absolute URLs
                if excel_url.startswith('http'):
                    # Absolute URL, use as is
                    pass
                else:
                    # Relative URL, join with base URL
                    excel_url = urljoin(self.base_url, excel_url)
                
                return {
                    'excel_url': excel_url,
                    'tournament_id': tournament_id,
                    'name': f'Tournament {tournament_id}',
                    'has_elo_calculation': False  # Default for fallback case
                }
            else:
                logger.warning(f"Could not find Excel export or final table link for tournament {tournament_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting tournament details for {tournament_id}: {str(e)}")
            return None

    def download_excel_export(self, tournament_details):
        """Download Excel export from tournament details"""
        try:
            tournament_id = tournament_details['tournament_id']
            
            # Try multiple methods to get Excel export
            excel_url = None
            
            # Method 1: Check for direct Excel URL
            if 'excel_url' in tournament_details:
                excel_url = tournament_details['excel_url']
                logger.info(f"Using direct Excel export URL for tournament {tournament_id}")
            
            # Method 2: Try to construct Excel URL from final table URL
            elif 'final_table_url' in tournament_details:
                final_table_url = tournament_details['final_table_url']
                logger.info(f"Trying to get Excel export from final table page for tournament {tournament_id}")
                
                # First try to find the link on the page
                response = self.session.get(final_table_url)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Check if we need to submit "Show tournament details" form again for this page
                show_details_button = soup.find('input', {'value': re.compile(r'Show tournament details', re.IGNORECASE)})
                if show_details_button:
                    logger.info(f"Found 'Show tournament details' button on final table page, submitting form...")
                    
                    # Find the form containing this button
                    form = show_details_button.find_parent('form')
                    if form:
                        # Get form action
                        action = form.get('action', '')
                        if not action.startswith('http'):
                            action = urljoin(final_table_url, action)
                        
                        # Prepare form data
                        form_data = {}
                        
                        # Get viewstate and other hidden fields
                        for hidden_input in form.find_all('input', type='hidden'):
                            name = hidden_input.get('name')
                            value = hidden_input.get('value', '')
                            if name:
                                form_data[name] = value
                        
                        # Add the button that was clicked
                        button_name = show_details_button.get('name')
                        button_value = show_details_button.get('value')
                        if button_name:
                            form_data[button_name] = button_value
                        
                        # Submit the form
                        response = self.session.post(action, data=form_data)
                        response.raise_for_status()
                        soup = BeautifulSoup(response.content, 'html.parser')
                        logger.info(f"Successfully submitted tournament details form on final table page for {tournament_id}")
                
                # Look for Excel export link on final table page
                excel_links = soup.find_all('a', string=re.compile(r'excel|xlsx|xls', re.IGNORECASE))
                if not excel_links:
                    # Try href patterns
                    excel_links = soup.find_all('a', href=re.compile(r'excel=', re.IGNORECASE))
                if not excel_links:
                    # Try alternative patterns
                    excel_links = soup.find_all('a', href=re.compile(r'\.xlsx?$', re.IGNORECASE))
                
                if excel_links:
                    href = excel_links[0].get('href')
                    # Handle both relative and absolute URLs
                    if href.startswith('http'):
                        excel_url = href
                    else:
                        excel_url = urljoin(self.base_url, href)
                    logger.info(f"Found Excel export link on final table page: {excel_url}")
                else:
                    # Method 3: Construct Excel URL based on crosstable pattern
                    # Pattern for crosstable with round results: base_url + ?lan=0&zeilen=0&art=4&turdet=YES&prt=4&excel=2010
                    base_url = final_table_url.split('?')[0]  # Remove existing parameters
                    excel_url = f"{base_url}?lan=0&zeilen=0&art=4&turdet=YES&prt=4&excel=2010"
                    logger.info(f"Constructed crosstable Excel export URL for tournament {tournament_id}: {excel_url}")
            else:
                logger.error(f"No Excel export method available for tournament {tournament_id}")
                return None
            
            # Download the Excel file
            excel_response = self.session.get(excel_url)
            excel_response.raise_for_status()
            
            # Check if response is actually an Excel file
            content_type = excel_response.headers.get('content-type', '').lower()
            if 'excel' not in content_type and 'spreadsheet' not in content_type:
                # Check if content looks like Excel (starts with PK for ZIP-based files)
                if not excel_response.content.startswith(b'PK'):
                    logger.warning(f"Response may not be Excel file. Content-Type: {content_type}")
                    # Still try to save it, sometimes the content-type is wrong
            
            # Save to temporary location
            filename = f"tournament_{tournament_id}.xlsx"
            filepath = os.path.join('/tmp', filename)
            
            with open(filepath, 'wb') as f:
                f.write(excel_response.content)
            
            logger.info(f"Downloaded Excel file for tournament {tournament_id}: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error downloading Excel export for tournament {tournament_id}: {str(e)}")
            return None

    def download_cross_table_excel(self, tournament_details):
        """Download cross table Excel export with round-by-round results"""
        try:
            tournament_id = tournament_details['tournament_id']
            
            # Extract base URL from final table URL
            final_table_url = tournament_details.get('final_table_url', '')
            if '?' in final_table_url:
                base_url = final_table_url.split('?')[0]
            else:
                base_url = final_table_url
            
            # Construct cross table Excel URL (art=2 for pairings/results)
            cross_table_excel_url = f"{base_url}?lan=1&art=2&prt=4&excel=2010"
            logger.info(f"Attempting to download cross table Excel for tournament {tournament_id}")
            logger.info(f"Cross table URL: {cross_table_excel_url}")
            
            response = self.session.get(cross_table_excel_url)
            response.raise_for_status()
            
            # Save to temporary file
            filename = f"cross_table_{tournament_id}.xlsx"
            filepath = os.path.join('/tmp', filename)
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"Downloaded cross table Excel file for tournament {tournament_id}: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error downloading cross table Excel for tournament {tournament_id}: {str(e)}")
            return None

    def check_elo_calculation(self, tournament_url, tournament_id):
        """Check if tournament has ELO calculation by looking for Rating calculation field"""
        try:
            response = self.session.get(tournament_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Strategy 1: Check if there's a "Turnierdetails anzeigen" / "Show tournament details" link
            details_link = None
            for link in soup.find_all('a'):
                link_text = link.get_text(strip=True).lower()
                if ('turnierdetails anzeigen' in link_text or 
                    'show tournament details' in link_text or
                    'tournament details' in link_text):
                    details_link = link
                    break
            
            if details_link:
                details_href = details_link.get('href')
                if details_href:
                    # Convert relative URL to absolute if needed
                    if not details_href.startswith('http'):
                        from urllib.parse import urljoin
                        details_url = urljoin(tournament_url, details_href)
                    else:
                        details_url = details_href
                    
                    logger.info(f"Found tournament details link for {tournament_id}, following: {details_url}")
                    
                    # Follow the details link
                    details_response = self.session.get(details_url)
                    details_response.raise_for_status()
                    soup = BeautifulSoup(details_response.content, 'html.parser')
            
            # Strategy 2: Check if we need to submit the "Show tournament details" form (fallback)
            details_button = soup.find('input', {'name': 'cb_alleDetails', 'type': 'submit'})
            if details_button:
                logger.info(f"Found 'Show tournament details' button for rating check of tournament {tournament_id}, submitting form...")
                
                # Get form data for submission
                form = details_button.find_parent('form')
                if form:
                    form_data = {}
                    
                    # Get all hidden inputs
                    for hidden_input in form.find_all('input', type='hidden'):
                        name = hidden_input.get('name')
                        value = hidden_input.get('value', '')
                        if name:
                            form_data[name] = value
                    
                    # Add the button click
                    form_data['cb_alleDetails'] = details_button.get('value', 'Show tournament details')
                    
                    # Submit the form
                    response = self.session.post(tournament_url, data=form_data)
                    response.raise_for_status()
                    soup = BeautifulSoup(response.content, 'html.parser')
                    logger.info(f"Successfully submitted tournament details form for rating check of {tournament_id}")
                    
                    # After form submission, check if there's now a tournament details link
                    details_link_after_form = None
                    for link in soup.find_all('a'):
                        link_text = link.get_text(strip=True).lower()
                        if ('turnierdetails anzeigen' in link_text or 
                            'show tournament details' in link_text or
                            'tournament details' in link_text):
                            details_link_after_form = link
                            break
                    
                    if details_link_after_form:
                        details_href = details_link_after_form.get('href')
                        if details_href:
                            # Convert relative URL to absolute if needed
                            if not details_href.startswith('http'):
                                from urllib.parse import urljoin
                                details_url = urljoin(tournament_url, details_href)
                            else:
                                details_url = details_href
                            
                            logger.info(f"Found tournament details link after form submission for {tournament_id}, following: {details_url}")
                            
                            # Follow the details link
                            details_response = self.session.get(details_url)
                            details_response.raise_for_status()
                            soup = BeautifulSoup(details_response.content, 'html.parser')
            
            # Now look for rating calculation sections in both German and English
            # Strategy A: Look for specific rating patterns in the full page text
            page_text = soup.get_text()
            
            # Check for clear "no rating" indicators first
            if re.search(r'elorechnung\s*[-−‐]', page_text, re.IGNORECASE):
                logger.info(f"Tournament {tournament_id} has no rating calculation: found 'Elorechnung -'")
                return False
            elif re.search(r'rating\s*calculation\s*[-−‐]', page_text, re.IGNORECASE):
                logger.info(f"Tournament {tournament_id} has no rating calculation: found 'Rating calculation -'")
                return False
            
            # Check for clear "has rating" indicators
            # Look for patterns like "Elorechnung Elo international", "Rating calculation Rating national", etc.
            if re.search(r'elorechnung.{0,20}(elo\s+)?(international|national|intnational)', page_text, re.IGNORECASE):
                logger.info(f"Tournament {tournament_id} has rating calculation: found Elorechnung with international/national")
                return True
            elif re.search(r'rating\s*calculation.{0,50}(rating\s+)?(international|national)', page_text, re.IGNORECASE):
                logger.info(f"Tournament {tournament_id} has rating calculation: found Rating calculation with international/national")
                return True
            elif re.search(r'elorechnung\s*(yes|ja|berechnet)', page_text, re.IGNORECASE):
                logger.info(f"Tournament {tournament_id} has rating calculation: found positive Elorechnung")
                return True
            elif re.search(r'rating\s*calculation\s*(yes|ja|berechnet)', page_text, re.IGNORECASE):
                logger.info(f"Tournament {tournament_id} has rating calculation: found positive Rating calculation")
                return True
            
            # Strategy B: Look in structured elements
            rating_patterns = [
                r'Elorechnung',  # German
                r'Rating calculation',  # English
                r'Elo-?rechnung',  # German with optional hyphen
                r'ELO.*calculation',  # English variants
                r'rating\s*calculation',  # Case variations
            ]
            
            for pattern in rating_patterns:
                # Look for text containing the rating pattern
                rating_elements = soup.find_all(text=re.compile(pattern, re.IGNORECASE))
                
                for elo_text in rating_elements:
                    # Get the parent element and its siblings to find the value
                    parent = elo_text.parent
                    if parent:
                        # Get the full row/context containing this text
                        parent_row = parent.find_parent('tr') or parent
                        full_text = parent_row.get_text().strip()
                        
                        logger.debug(f"Found rating section for {tournament_id}: '{full_text}'")
                        
                        # Look for dash indicating no rating calculation
                        if re.search(r'(rating\s*calculation|elorechnung)\s*[-−‐]', full_text, re.IGNORECASE):
                            logger.info(f"Tournament {tournament_id} has no rating calculation: '{full_text}'")
                            return False
                        elif re.search(r'(rating\s*calculation|elorechnung)\s*(yes|ja|berechnet)', full_text, re.IGNORECASE):
                            logger.info(f"Tournament {tournament_id} has rating calculation: '{full_text}'")
                            return True
            
            # Strategy 2: Look for "Parameters" link and check parameters page for more detailed info
            params_link = soup.find('a', href=re.compile(r'tnr.*art=0'))
            if params_link:
                params_url = params_link.get('href')
                if not params_url.startswith('http'):
                    params_url = urljoin(self.base_url, params_url)
                
                logger.debug(f"Found parameters page for {tournament_id}: {params_url}")
                
                try:
                    # Get the parameters page
                    params_response = self.session.get(params_url)
                    params_response.raise_for_status()
                    params_soup = BeautifulSoup(params_response.content, 'html.parser')
                    
                    # Look for rating calculation in parameters page
                    for pattern in rating_patterns:
                        rating_elements = params_soup.find_all(text=re.compile(pattern, re.IGNORECASE))
                        
                        for elo_text in rating_elements:
                            parent = elo_text.parent
                            if parent:
                                parent_row = parent.find_parent('tr') or parent
                                full_text = parent_row.get_text().strip()
                                
                                logger.debug(f"Found rating section on parameters page for {tournament_id}: '{full_text}'")
                                
                                if re.search(r'(rating\s*calculation|elorechnung)\s*[-−‐]', full_text, re.IGNORECASE):
                                    logger.info(f"Tournament {tournament_id} has no rating calculation (from parameters page): '{full_text}'")
                                    return False
                                elif re.search(r'(rating\s*calculation|elorechnung)\s*(yes|ja|berechnet)', full_text, re.IGNORECASE):
                                    logger.info(f"Tournament {tournament_id} has rating calculation (from parameters page): '{full_text}'")
                                    return True
                except Exception as e:
                    logger.debug(f"Could not check parameters page for {tournament_id}: {e}")
            
            # If no specific rating information found, be conservative and don't import
            # This prevents unrated tournaments from being imported when rating status is unclear
            logger.info(f"Tournament {tournament_id} - rating calculation status not found, assuming no (being conservative)")
            return False
            
        except Exception as e:
            logger.error(f"Error checking ELO calculation for tournament {tournament_id}: {str(e)}")
            return False

    def import_tournament_from_excel_file(self, filepath, tournament_name, tournament_id):
        """Import tournament using the tournament_importer module"""
        try:
            # Generate checksum for the file
            sha256 = hashlib.sha256()
            with open(filepath, 'rb') as f:
                while chunk := f.read(8192):
                    sha256.update(chunk)
            checksum = sha256.hexdigest()

            # Check if tournament already imported
            if Tournament.query.filter_by(checksum=checksum).first():
                logger.info(f"Tournament {tournament_id} already imported (checksum match)")
                return {'success': False, 'reason': 'already_imported'}

            # Use the tournament_importer module
            result = import_tournament_from_excel(
                filepath, 
                tournament_name=tournament_name,
                location="Austria",  # Default for Austrian federation
                date=datetime.now().date(),  # Will be extracted from file if available
                checksum=checksum,
                chess_results_id=tournament_id,
                chess_results_url=f"https://chess-results.com/tnr{tournament_id}.aspx"
            )
            
            logger.info(f"Successfully imported tournament {tournament_id}: {result['tournament_name']}")
            logger.info(f"  Imported {result['imported_players']} players, {result['imported_games']} games")
            
            return result
            
        except Exception as e:
            logger.error(f"Error importing tournament {tournament_id}: {str(e)}")
            return {'success': False, 'reason': str(e)}

    def tournament_exists(self, tournament_id, tournament_name):
        """Check if tournament already exists in database"""
        try:
            # Create a checksum for the tournament
            checksum_data = f"{tournament_id}_{tournament_name}"
            checksum = hashlib.md5(checksum_data.encode()).hexdigest()
            
            existing = Tournament.query.filter_by(checksum=checksum).first()
            return existing is not None
        except Exception as e:
            logger.error(f"Error checking if tournament exists: {str(e)}")
            return False
            
            # Save players
            for player_data in tournament_data['players']:
                tournament_player = TournamentPlayer(
                    tournament_id=tournament.id,
                    name=player_data.get('name'),
                    rank=player_data.get('rank'),
                    points=player_data.get('points'),
                    # You can add more fields as needed
                )
                db.session.add(tournament_player)
            
            db.session.commit()
            logger.info(f"Saved tournament {tournament_id} with {len(tournament_data['players'])} players")
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error saving tournament data: {str(e)}")
            return False

    def crawl_finished_tournaments(self):
        """Main crawling function that orchestrates the complete workflow"""
        try:
            logger.info("Starting chess-results.com crawler")
            
            # Step 1: Login
            if not self.login():
                logger.error("Failed to login, aborting crawler")
                return 0
            
            # Step 2: Get list of finished tournaments
            tournaments = self.get_finished_tournaments()
            if not tournaments:
                logger.info("No finished tournaments found")
                return 0
            
            logger.info(f"Found {len(tournaments)} finished tournaments")
            processed_count = 0
            
            # Step 3: Process each tournament
            for tournament in tournaments:
                tournament_id = tournament['id']
                tournament_name = tournament['name']
                tournament_url = tournament['url']
                
                logger.info(f"Processing tournament: {tournament_name} (ID: {tournament_id})")
                
                # Step 3.1: Check if tournament already imported by chess_results_id
                existing_tournament = Tournament.query.filter_by(chess_results_id=tournament_id).first()
                if existing_tournament:
                    logger.info(f"Tournament {tournament_id} already imported (ID match: {existing_tournament.name})")
                    continue
                
                # Step 4: Check if tournament has ELO calculation
                if not self.check_elo_calculation(tournament_url, tournament_id):
                    logger.info(f"Skipping tournament {tournament_id} - no ELO calculation")
                    continue
                
                # Step 5: Get tournament details and final table URL
                tournament_details = self.get_tournament_details(tournament_url, tournament_id)
                if not tournament_details:
                    logger.warning(f"Could not get details for tournament {tournament_id}")
                    continue
                
                # Step 6: Download Excel export
                excel_file = self.download_excel_export(tournament_details)
                if not excel_file:
                    logger.warning(f"Could not download Excel file for tournament {tournament_id}")
                    continue
                
                # Step 7: Import tournament using the tournament_importer module
                result = self.import_tournament_from_excel_file(excel_file, tournament_name, tournament_id)
                
                # Clean up the temporary file
                if os.path.exists(excel_file):
                    os.remove(excel_file)
                
                if result.get('success'):
                    processed_count += 1
                    logger.info(f"Successfully processed tournament {tournament_id}")
                else:
                    logger.warning(f"Failed to import tournament {tournament_id}: {result.get('reason', 'unknown error')}")
                
                # Add a small delay to be respectful to the server
                time.sleep(2)
            
            logger.info(f"Crawling completed. Successfully processed {processed_count} new tournaments")
            return processed_count
            
        except Exception as e:
            logger.error(f"Error in crawling process: {str(e)}")
            return 0


def run_crawler():
    """Standalone function to run the crawler"""
    crawler = ChessResultsCrawler()
    return crawler.crawl_finished_tournaments()


def setup_logging():
    """Setup logging for the crawler"""
    log_dir = os.path.join(os.path.dirname(__file__), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, 'crawler.log')
    
    # Create file handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)


if __name__ == "__main__":
    # For standalone execution
    setup_logging()
    
    try:
        from app import create_app
        
        app = create_app()
        with app.app_context():
            logger.info("Starting scheduled crawler run")
            processed = run_crawler()
            logger.info(f"Crawler run completed. Processed {processed} tournaments")
    except Exception as e:
        logger.error(f"Failed to run crawler: {str(e)}")
        raise
