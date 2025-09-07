import requests
import pandas as pd
import re
import os
import time
import logging
import hashlib
import tempfile
from datetime import datetime, timedelta, date
from urllib.parse import urljoin, urlparse, parse_qs
from bs4 import BeautifulSoup
from db.models import db, Tournament, TournamentPlayer, Player
from sqlalchemy import func

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

    def click_show_tournament_details_button(self, soup, tournament_url, tournament_id, need_details=False):
        """
        Click the "Show tournament details" button if it exists on the page.
        Returns the updated soup object after the button click, or None if no button found.
        """

        time.sleep(2)

        details_button = soup.find('input', {'name': 'cb_alleDetails', 'type': 'submit'})
        if not details_button:
            return None
            
        logger.info(f"Found 'Show tournament details' button for tournament {tournament_id}, submitting form...")
        
        # Get form data for submission
        form = details_button.find_parent('form')
        if not form:
            logger.warning(f"Could not find form for details button for tournament {tournament_id}")
            return None
            
        form_data = {}
        
        # Get all hidden inputs
        for hidden_input in form.find_all('input', type='hidden'):
            name = hidden_input.get('name')
            value = hidden_input.get('value', '')
            if name:
                form_data[name] = value
        
        # Get the name of the first submit button
        submit_button = form.find('input', {'type': 'submit'})
        if submit_button:
            form_data[submit_button.get('name')] = submit_button.get('value', 'Show tournament details')

        # Get form action and resolve it properly
        form_action = form.get('action', '')
        if form_action:
            if not form_action.startswith('http'):
                from urllib.parse import urljoin
                submit_url = urljoin(tournament_url, form_action)
            else:
                submit_url = form_action
        else:
            submit_url = tournament_url
        
        if need_details:
            if '?' in submit_url:
                submit_url = submit_url + '&turdet=YES'
            else:
                submit_url = submit_url + '?turdet=YES'
        else:
            if 'turdet=YES' in submit_url:
                submit_url = submit_url.replace('turdet=YES', '').rstrip('&').rstrip('?')

        # Fix any double ampersands that might have been introduced
        submit_url = submit_url.replace('&&', '&')

        logger.info(f"Submitting form to: {submit_url}")

        # Submit the form to the correct URL
        response = self.session.post(submit_url, data=form_data)
        response.raise_for_status()
        new_soup = BeautifulSoup(response.content, 'html.parser')
        logger.info(f"Successfully submitted tournament details form for {tournament_id}")
        
        return new_soup
            
    def _parse_tournament_metadata(self, soup, tournament_id):
        """Parse tournament metadata like elo rating, date, location, type, time control"""
        metadata = {
            'id': tournament_id,
            'tournament_url': f"https://chess-results.com/tnr{tournament_id}.aspx",
            'name': f"Tournament {tournament_id}",
            'date': date.today().strftime("%Y-%m-%d"),
            'location': "Earth",
            'tournament_type': None,
            'time_control': None,
            'elo_calculation': None,
            'number_of_rounds': None
        }

        try:
            for row in soup.find_all('tr'):
                # If the row contains 2 <td> elements, we have a key-value pair
                cols = row.find_all('td')
                if len(cols) == 2:
                    key = cols[0].get_text(strip=True).lower()
                    value = cols[1].get_text(strip=True)
                    
                    if 'elo' in key or 'elorechnung' in key or 'rating calculation' in key:
                        if value == '' or value == '-':
                            metadata['elo_calculation'] = None
                        else:
                            metadata['elo_calculation'] = value.strip()
                    
                    elif 'datum' in key or 'date' in key or 'beginn' in key or 'start' in key or 'from' in key or 'vom' in key:
                        if value and value.strip():
                            metadata['date'] = value.strip()
                            # sometimes, date is in fromat "2019/09/07 to 2019/09/08", just retain the start date
                            if ' to ' in metadata['date']:
                                metadata['date'] = metadata['date'].split(' to ')[0]
                            if ' bis ' in metadata['date']:
                                metadata['date'] = metadata['date'].split(' bis ')[0]
                            for fmt in ("%d.%m.%Y", "%Y/%m/%d", "%Y-%m-%d", "%d/%m/%Y"):
                                try:
                                    parsed_date = datetime.strptime(metadata['date'], fmt)
                                    metadata['date'] = parsed_date.strftime("%Y-%m-%d")
                                    break
                                except ValueError:
                                    continue
                            logger.info(f"Found date for tournament {tournament_id}: {metadata['date']}")
                    
                    elif 'ort' in key or 'location' in key or 'venue' in key or 'place' in key or 'austragungsort' in key:
                        if value and value.strip():
                            metadata['location'] = value.strip()
                            logger.info(f"Found location for tournament {tournament_id}: {metadata['location']}")
                    
                    elif 'modus' in key or 'turniermodus' in key or 'tournament type' in key:
                        if value and value.strip():
                            metadata['tournament_type'] = value.strip()
                            logger.info(f"Found tournament type for tournament {tournament_id}: {metadata['tournament_type']}")
                    
                    elif 'bedenkzeit' in key or 'time control' in key:
                        logger.info(f"Found time control entry for tournament {tournament_id}: '{value}'")
                        if value and value.strip():
                            metadata['time_control'] = value.strip()
                            logger.info(f"Found time control for tournament {tournament_id}: {metadata['time_control']}")
                    
                    elif 'Number of rounds' in key or 'rundenanzahl' in key or 'rounds' in key:
                        if value and value.strip():
                            metadata['number_of_rounds'] = value.strip()
                            logger.info(f"Found number of rounds for tournament {tournament_id}: {metadata['number_of_rounds']}")

            logger.info(f"Parsed metadata for tournament {tournament_id}: {metadata}")

            # Look for tournament name in headers (may be more detailed than title)
            headers = soup.find_all(['h2'])
            for header in headers:
                text = header.get_text() if header else None
                if text and text.strip() and len(text.strip()) > 5 and 'chess-results' not in text.lower():
                    text = text.strip()
                    # Skip generic messages/notes
                    skip_keywords = ['note:', 'reduce', 'server load', 'search engines', 'google', 'yahoo', 'button']
                    if any(skip_word in text.lower() for skip_word in skip_keywords):
                        continue
                        
                    # Prefer headers that are longer and contain more detail than the title
                    if not metadata['name'] or len(text) > len(metadata['name']):
                        metadata['name'] = text
                        logger.info(f"Found tournament name: {metadata['name']}")
                        break
            
            # Fallback to ID-based name if nothing found
            if not metadata['name'] or len(metadata['name']) < 3:
                metadata['name'] = f'Tournament {tournament_id}'
                            
        except Exception as e:
            logger.error(f"Error parsing tournament metadata for {tournament_id}: {e}")
            
        return metadata

    def get_tournament_details(self, tournament_url, tournament_id):
        """Get tournament details and check if it should be processed"""
        try:
            response = self.session.get(tournament_url, allow_redirects=True)
            response.raise_for_status()
            
            # Update tournament_url to the redirected URL
            actual_tournament_url = response.url
            if actual_tournament_url != tournament_url:
                logger.info(f"Tournament URL redirected from {tournament_url} to {actual_tournament_url}")
                tournament_url = actual_tournament_url
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Check if we need to submit the "Show tournament details" form (anti-crawling measure)
            updated_soup = self.click_show_tournament_details_button(soup, tournament_url, tournament_id, True)
            if updated_soup:
                soup = updated_soup
            else:
                # If no button, try appending turdet=YES directly to the URL
                if '?' in tournament_url:
                    tournament_url_with_details = tournament_url + '&turdet=YES'
                else:
                    tournament_url_with_details = tournament_url + '?turdet=YES'
                
                logger.info(f"No details button found, trying direct URL approach with turdet=YES: {tournament_url_with_details}")
                response = self.session.get(tournament_url_with_details)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')
            
            logger.info(f"Accessed tournament page for {tournament_id}, parsing metadata...")

            # Parse tournament metadata
            tournament_metadata = self._parse_tournament_metadata(soup, tournament_id)

            # Team tournament detection: Search for any <a> with a text that contains "Teamaufstellung" or "Team composition"
            tournament_metadata['is_team_tournament'] = False
            team_link = soup.find('a', string=re.compile(r'Teamaufstellung|Team composition', re.IGNORECASE))
            if team_link:
                tournament_metadata['is_team_tournament'] = True
                logger.info(f"Tournament {tournament_id} detected as team tournament based on link text.")
            
            # If this is a team tournament, search for the "Team Composition with round results" or "Teamaufstellung mit Einzelergebnissen" link
            if tournament_metadata['is_team_tournament']:
                team_composition_link = soup.find('a', string=re.compile(r'Team Composition with round results|Teamaufstellung mit Einzelergebnissen', re.IGNORECASE))
                if team_composition_link:
                    href = team_composition_link.get('href')
                    if href:
                        full_url = href if href.startswith('http') else urljoin(self.base_url, href)
                        logger.info(f"Found Team Composition link for tournament {tournament_id}: {full_url}")

                        # follow the link
                        response = self.session.get(full_url)
                        response.raise_for_status()
                        soup = BeautifulSoup(response.content, 'html.parser')

                        # Check if we need to submit the "Show tournament details" form (anti-crawling measure)
                        updated_soup = self.click_show_tournament_details_button(soup, tournament_url, tournament_id)
                        if updated_soup:
                            soup = updated_soup

                        # Find the Excel export link
                        excel_link = soup.find('a', string=re.compile(r'Excel', re.IGNORECASE))
                        if excel_link:
                            tournament_metadata['excel_url'] = excel_link.get('href')
                            logger.info(f"Found Excel export link for tournament {tournament_id}: {tournament_metadata['excel_url']}")
   
                    else:
                        logger.info(f"Team Composition link found but no href for tournament {tournament_id}")
                else:
                    logger.info(f"No Team Composition link found for team tournament {tournament_id}")

            else:
                end_table_link = soup.find('a', string=re.compile(r'Endtabelle nach|Final ranking crosstable after', re.IGNORECASE))
                if end_table_link:
                    href = end_table_link.get('href')
                    if href:
                        full_url = href if href.startswith('http') else urljoin(self.base_url, href)
                        logger.info(f"Found End Table link for tournament {tournament_id}: {full_url}")

                        # follow the link
                        response = self.session.get(full_url)
                        response.raise_for_status()
                        soup = BeautifulSoup(response.content, 'html.parser')

                        # Check if we need to submit the "Show tournament details" form (anti-crawling measure)
                        # Use the actual response URL, not the original tournament_url
                        updated_soup = self.click_show_tournament_details_button(soup, response.url, tournament_id)
                        if updated_soup:
                            soup = updated_soup

                        # Find the Excel export link
                        excel_link = soup.find('a', string=re.compile(r'Excel', re.IGNORECASE))
                        if excel_link:
                            tournament_metadata['excel_url'] = excel_link.get('href')
                            logger.info(f"Found Excel export link for tournament {tournament_id}: {tournament_metadata['excel_url']}")

                    else:
                        logger.info(f"End Table link found but no href for tournament {tournament_id}")
                else:
                    logger.info(f"No End Table link found for tournament {tournament_id}")

            # Return the metadata and the URL to the final table or Excel export if found
            return tournament_metadata

        except Exception as e:
            logger.error(f"Error getting tournament details for {tournament_id}: {str(e)}")
            return None

    def download_excel_export(self, tournament_details):
        """Download Excel export from tournament details"""
        try:
            if not 'excel_url' in tournament_details:
                logger.error("No Excel export URL found in tournament details")
                return None
            
            # Download the Excel file
            excel_response = self.session.get(tournament_details['excel_url'])
            excel_response.raise_for_status()
            
            # Check if response is actually an Excel file
            content_type = excel_response.headers.get('content-type', '').lower()
            if 'excel' not in content_type and 'spreadsheet' not in content_type:
                # Check if content looks like Excel (starts with PK for ZIP-based files)
                if not excel_response.content.startswith(b'PK'):
                    logger.warning(f"Response may not be Excel file. Content-Type: {content_type}")
                    # Still try to save it, sometimes the content-type is wrong
            
            # Save to temporary location
            filename = f"tournament_{tournament_details['id']}.xlsx"
            filepath = os.path.join('/tmp', filename)
            
            with open(filepath, 'wb') as f:
                f.write(excel_response.content)

            logger.info(f"Downloaded Excel file for tournament {tournament_details['id']}: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error downloading Excel export for tournament {tournament_details['id']}: {str(e)}")
            return None
