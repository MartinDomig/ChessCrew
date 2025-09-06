#!/usr/bin/env python3
"""
Test for Team Tournament with Individual Player Results - Breitler, Jakob Case

This test verifies that the tournament results crawler can correctly handle team tournaments
and extract individual player results from the "Team Composition with round-results" page.

Specific test case: Tournament 999318 - Vorarlberger Landesmannschaftsmeisterschaft 2024-25, LIGA
URL: https://s1.chess-results.com/tnr999318.aspx

Expected result: Breitler, Jakob should have 1.5 points out of 5 games.

The crawler must:
1. Click "Show tournament details" button to reveal navigation links
2. Find and navigate to "Team Composition with round-results" page  
3. Extract individual player results including Breitler, Jakob's 1.5/5 score
4. Import individual games and results correctly
"""

import sys
import os
import logging
from datetime import datetime
import tempfile
import pandas as pd

# Add backend to path
sys.path.append('/home/martin/chesscrew/backend')

from app import create_app
from db.models import db, Tournament, TournamentPlayer, Game, Player
from chess_results_crawler import ChessResultsCrawler

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_team_tournament_breitler_jakob():
    """Test Breitler, Jakob team tournament with individual player results"""
    
    print("🧪 Testing Team Tournament - Breitler, Jakob Case")
    print("=" * 80)
    print("URL: https://s1.chess-results.com/tnr999318.aspx")
    print("Expected: Breitler, Jakob with 1.5 points out of 5 games")
    print("Requirements: Navigate via 'Team Composition with round-results'")
    print()
    
    try:
        # Clear database first to ensure clean test
        print("🧹 Clearing database...")
        Game.query.delete()
        TournamentPlayer.query.delete() 
        Tournament.query.delete()
        db.session.commit()
        print("✅ Database cleared")
        print()
        
        # Initialize crawler
        print("🔧 Initializing crawler...")
        crawler = ChessResultsCrawler()
        
        # Login to chess-results.com (required for some team tournaments)
        print("🔐 Logging in to chess-results.com...")
        login_success = crawler.login()
        if not login_success:
            print("⚠️  Login failed, proceeding without login (may limit access)")
        else:
            print("✅ Successfully logged in")
        print()
        
        # Test: Download team tournament with individual results
        print("📥 Downloading team tournament with individual results...")
        print("-" * 50)
        
        tournament_url = "https://s1.chess-results.com/tnr999318.aspx"
        tournament_id = "999318"
        
        # Step 1: Get tournament details (this handles "Show tournament details" button)
        print("📋 Getting tournament details...")
        tournament_details = crawler.get_tournament_details(tournament_url, tournament_id)
        
        if not tournament_details:
            print("❌ Failed to get tournament details!")
            return False
        
        print(f"✅ Tournament details retrieved: {tournament_details.get('name', 'Unknown')}")
        print()
        
        # Step 2: Navigate to team composition page with individual results
        print("🔍 Looking for team composition with round-results...")
        team_composition_url = get_team_composition_url(crawler, tournament_url, tournament_id)
        
        if not team_composition_url:
            print("❌ Could not find team composition with round-results page!")
            return False
        
        print(f"✅ Found team composition page: {team_composition_url}")
        print()
        
        # Step 3: Download Excel export from team composition page
        print("📊 Downloading team composition Excel export...")
        excel_path = download_team_composition_excel(crawler, team_composition_url, tournament_id)
        
        if not excel_path:
            print("❌ Failed to download team composition Excel!")
            return False
        
        print(f"✅ Downloaded team composition Excel: {excel_path}")
        print()
        
        # Step 4: Import the tournament data
        print("📥 Importing team tournament data...")
        result = crawler.import_tournament_from_excel_file(
            excel_path,
            "Vorarlberger Landesmannschaftsmeisterschaft 2024-25, LIGA",
            tournament_id
        )
        
        if not result or not result.get('success', False):
            print(f"❌ Failed to import tournament! {result}")
            return False
        
        print("✅ Tournament imported successfully")
        print()
        
        # Step 5: Verify Breitler, Jakob's data
        print("🔍 Verifying Breitler, Jakob's results...")
        print("-" * 40)
        
        tournament = Tournament.query.filter_by(chess_results_id='999318').first()
        if not tournament:
            print("❌ Tournament not found in database!")
            return False
        
        # Find Breitler, Jakob (who should have 1.5 points out of 5 games)
        target_player = None
        players = TournamentPlayer.query.filter_by(tournament_id=tournament.id).all()
        
        for player in players:
            player_name = player.name.lower()
            # Look for "Breitler, Jakob" 
            if 'breitler' in player_name and 'jakob' in player_name:
                target_player = player
                break
        
        if not target_player:
            print("❌ Breitler, Jakob not found in tournament!")
            print("Available players (first 20):")
            for i, p in enumerate(players[:20]):
                print(f"   {i+1}. {p.name}: {p.points} pts")
            print("...")
            return False
        
        print(f"✅ Found Breitler, Jakob: {target_player.name}")
        print(f"   Points: {target_player.points}")
        print()
        
        # Verify the expected results
        expected_points = 1.5
        expected_games = 5
        
        # Count games for Breitler, Jakob
        player_games = Game.query.filter_by(
            tournament_id=tournament.id, 
            player_id=target_player.id
        ).all()
        
        actual_games = len(player_games)
        actual_points = target_player.points
        
        print("🎯 Verification Results:")
        print(f"   Expected Points: {expected_points}")
        print(f"   Actual Points: {actual_points}")
        print(f"   Expected Games: {expected_games}")
        print(f"   Actual Games: {actual_games}")
        print()
        
        # Validate results
        success = True
        
        if actual_points != expected_points:
            print(f"❌ POINTS MISMATCH: Expected {expected_points}, got {actual_points}")
            success = False
        else:
            print(f"✅ Points correct: {actual_points}")
        
        if actual_games != expected_games:
            print(f"❌ GAMES COUNT MISMATCH: Expected {expected_games}, got {actual_games}")
            success = False
        else:
            print(f"✅ Games count correct: {actual_games}")
        
        # Show game details
        if player_games:
            print()
            print("🎲 Breitler, Jakob's Games:")
            for i, game in enumerate(player_games, 1):
                opponent_name = "Unknown"
                if game.opponent_id:
                    opponent = TournamentPlayer.query.get(game.opponent_id)
                    if opponent:
                        opponent_name = opponent.name
                
                # Verify no color info for team tournaments
                if game.player_color is not None:
                    print(f"❌ TEAM TOURNAMENT GAME HAS COLOR: Round {game.round_number} has player_color={game.player_color}")
                    success = False
                
                print(f"   Round {game.round_number}: vs {opponent_name}")
                print(f"      Result: {game.result} (no color - team tournament)")
            
            # Additional verification: ensure all games have no color
            games_with_color = [g for g in player_games if g.player_color is not None]
            if games_with_color:
                print(f"❌ {len(games_with_color)} games have color information (should be None for team tournaments)")
                success = False
            else:
                print("✅ All games correctly have no color information (team tournament)")
        
        print()
        
        # Verify tournament is marked as team tournament
        if not tournament.is_team:
            print("❌ Tournament should be marked as team tournament!")
            success = False
        else:
            print("✅ Tournament correctly marked as team tournament")
        
        # Clean up temporary file
        if os.path.exists(excel_path):
            os.unlink(excel_path)
        
        if success:
            print()
            print("🎉 BREITLER, JAKOB TEAM TOURNAMENT TEST PASSED! ✅")
            print()
            print("📊 Summary:")
            print(f"   ✅ Tournament: {tournament.name}")
            print(f"   ✅ Breitler, Jakob found with {actual_points}/{expected_games} points")
            print(f"   ✅ Individual games imported: {actual_games}")
            print(f"   ✅ Team tournament correctly identified")
            print(f"   ✅ Team composition navigation working")
            return True
        else:
            print()
            print("❌ BREITLER, JAKOB TEAM TOURNAMENT TEST FAILED!")
            return False
        
        print(f"✅ Found Benjamin Höfel: {benjamin.name}")
        print(f"   Points: {benjamin.points}")
        print(f"   Rank: {benjamin.rank}")
        print()
        
        # Verify the expected results
        expected_points = 1.5
        expected_games = 5
        
        # Count games for Benjamin
        benjamin_games = Game.query.filter_by(
            tournament_id=tournament.id, 
            player_id=benjamin.id
        ).all()
        
        actual_games = len(benjamin_games)
        actual_points = benjamin.points
        
        print("🎯 Verification Results:")
        print(f"   Expected Points: {expected_points}")
        print(f"   Actual Points: {actual_points}")
        print(f"   Expected Games: {expected_games}")
        print(f"   Actual Games: {actual_games}")
        print()
        
        # Validate results
        success = True
        
        if actual_points != expected_points:
            print(f"❌ POINTS MISMATCH: Expected {expected_points}, got {actual_points}")
            success = False
        else:
            print(f"✅ Points correct: {actual_points}")
        
        if actual_games != expected_games:
            print(f"❌ GAMES COUNT MISMATCH: Expected {expected_games}, got {actual_games}")
            success = False
        else:
            print(f"✅ Games count correct: {actual_games}")
        
        # Show game details
        if benjamin_games:
            print()
            print("🎲 Benjamin Höfel's Games:")
            for i, game in enumerate(benjamin_games, 1):
                opponent_name = "Unknown"
                if game.opponent_id:
                    opponent = TournamentPlayer.query.get(game.opponent_id)
                    if opponent:
                        opponent_name = opponent.name
                
                print(f"   Round {game.round_number}: vs {opponent_name}")
                print(f"      Result: {game.result} ({'White' if game.color == 'w' else 'Black'})")
        
        print()
        
        # Verify tournament is marked as team tournament
        if not tournament.is_team:
            print("❌ Tournament should be marked as team tournament!")
            success = False
        else:
            print("✅ Tournament correctly marked as team tournament")
        
        # Clean up temporary file
        if os.path.exists(excel_path):
            os.unlink(excel_path)
        
        if success:
            print()
            print("🎉 BENJAMIN HÖFEL TEAM TOURNAMENT TEST PASSED! ✅")
            print()
            print("📊 Summary:")
            print(f"   ✅ Tournament: {tournament.name}")
            print(f"   ✅ Benjamin Höfel found with {actual_points}/{expected_games} points")
            print(f"   ✅ Individual games imported: {actual_games}")
            print(f"   ✅ Team tournament correctly identified")
            return True
        else:
            print()
            print("❌ BENJAMIN HÖFEL TEAM TOURNAMENT TEST FAILED!")
            return False
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def get_team_composition_url(crawler, tournament_url, tournament_id):
    """
    Navigate to tournament page and find the "Team Composition with round-results" link
    This requires first clicking "Show tournament details" to reveal navigation
    """
    try:
        print("🔍 Navigating to find team composition link...")
        
        # Get the main tournament page first (this should handle "Show tournament details")
        response = crawler.session.get(tournament_url)
        response.raise_for_status()
        
        from bs4 import BeautifulSoup
        import re
        from urllib.parse import urljoin
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Check if we need to submit "Show tournament details" form
        details_button = soup.find('input', {'name': 'cb_alleDetails', 'type': 'submit'}) or \
                        soup.find('input', {'value': re.compile(r'Show tournament details', re.IGNORECASE)})
        
        if details_button:
            print("   📋 Found 'Show tournament details' button, submitting...")
            
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
                button_name = details_button.get('name', 'cb_alleDetails')
                button_value = details_button.get('value', 'Show tournament details')
                form_data[button_name] = button_value
                
                # Submit the form
                response = crawler.session.post(tournament_url, data=form_data)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')
                print("   ✅ Successfully revealed tournament navigation")
        
        # Now look for team composition links
        print("   🔍 Looking for team composition links...")
        
        # Common patterns for team composition with round results
        composition_patterns = [
            r'team.*composition.*round.*result',
            r'mannschaftsaufstellung.*runden.*ergebnis',
            r'team.*comp.*round',
            r'aufstellung.*runden',
            r'composition.*round',
            r'team.*round.*result'
        ]
        
        # Look for links with these patterns
        all_links = soup.find_all('a', href=True)
        
        for link in all_links:
            link_text = link.get_text(strip=True).lower()
            href = link.get('href')
            
            # Check text patterns
            for pattern in composition_patterns:
                if re.search(pattern, link_text, re.IGNORECASE):
                    composition_url = href if href.startswith('http') else urljoin(tournament_url, href)
                    print(f"   ✅ Found team composition link: {link_text}")
                    return composition_url
        
        # Alternative: Look for art=20 parameter which is often used for team composition
        print("   🔍 Looking for art=20 (team composition) links...")
        for link in all_links:
            href = link.get('href')
            if 'art=20' in href:
                composition_url = href if href.startswith('http') else urljoin(tournament_url, href)
                print(f"   ✅ Found art=20 team composition link")
                return composition_url
        
        # Try constructing the URL manually
        print("   🔧 Attempting to construct team composition URL...")
        if '?' in tournament_url:
            base_url = tournament_url.split('?')[0]
        else:
            base_url = tournament_url
        
        # Try common team composition URL patterns
        test_urls = [
            f"{base_url}?art=20",  # Team composition
            f"{base_url}?art=20&prt=1",  # Team composition with details
            f"{base_url}?art=20&lan=1",  # Team composition in English
        ]
        
        for test_url in test_urls:
            try:
                test_response = crawler.session.get(test_url)
                if test_response.status_code == 200:
                    # Check if this page contains team/player data
                    test_content = test_response.text.lower()
                    if any(keyword in test_content for keyword in ['team', 'mannschaft', 'player', 'spieler']):
                        print(f"   ✅ Found working team composition URL: {test_url}")
                        return test_url
            except:
                continue
        
        print("   ❌ Could not find team composition with round-results link")
        return None
        
    except Exception as e:
        print(f"   ❌ Error finding team composition URL: {e}")
        return None

def download_team_composition_excel(crawler, team_composition_url, tournament_id):
    """
    Download Excel export from the team composition page
    """
    try:
        print("📊 Downloading Excel from team composition page...")
        
        # Navigate to team composition page
        response = crawler.session.get(team_composition_url)
        response.raise_for_status()
        
        from bs4 import BeautifulSoup
        import re
        from urllib.parse import urljoin
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Check for "Show tournament details" button on this page too
        details_button = soup.find('input', {'value': re.compile(r'Show tournament details', re.IGNORECASE)})
        if details_button:
            print("   📋 Found 'Show tournament details' on team composition page, submitting...")
            
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
                button_name = details_button.get('name')
                button_value = details_button.get('value')
                if button_name:
                    form_data[button_name] = button_value
                
                # Submit the form
                response = crawler.session.post(team_composition_url, data=form_data)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')
                print("   ✅ Revealed team composition details")
        
        # Look for Excel export link
        print("   🔍 Looking for Excel export link...")
        excel_links = soup.find_all('a', string=re.compile(r'excel|xlsx|xls', re.IGNORECASE))
        if not excel_links:
            # Try href patterns
            excel_links = soup.find_all('a', href=re.compile(r'excel=', re.IGNORECASE))
        
        excel_url = None
        if excel_links:
            href = excel_links[0].get('href')
            excel_url = href if href.startswith('http') else urljoin(team_composition_url, href)
            print(f"   ✅ Found Excel export link: {excel_url}")
        else:
            # Try to construct Excel URL using the base URL pattern
            print("   🔧 Constructing Excel export URL...")
            base_url = team_composition_url.split('?')[0] if '?' in team_composition_url else team_composition_url
            
            # Try different Excel export patterns for team composition
            test_excel_urls = [
                f"{base_url}?lan=1&art=1&prt=4&excel=2010",  # Team composition with Excel
                f"{base_url}?art=1&excel=2010",              # Simplified version
                f"{base_url}?art=1&prt=4&excel=2010",        # Without language parameter
            ]
            
            for test_url in test_excel_urls:
                try:
                    test_response = crawler.session.get(test_url)
                    if test_response.status_code == 200:
                        # Check if it's actually an Excel file
                        content_type = test_response.headers.get('content-type', '').lower()
                        if ('excel' in content_type or 'spreadsheet' in content_type or 
                            test_response.content.startswith(b'PK')):  # Excel files start with PK
                            excel_url = test_url
                            print(f"   ✅ Found working Excel URL: {excel_url}")
                            break
                except:
                    continue
        
        if not excel_url:
            print("   ❌ Could not find valid Excel export URL")
            return None
        
        # Download the Excel file
        print("   📥 Downloading Excel file...")
        excel_response = crawler.session.get(excel_url)
        excel_response.raise_for_status()
        
        # Verify it's actually an Excel file
        content_type = excel_response.headers.get('content-type', '').lower()
        if not ('excel' in content_type or 'spreadsheet' in content_type or 
                excel_response.content.startswith(b'PK')):
            print(f"   ❌ Downloaded file is not Excel format (Content-Type: {content_type})")
            # Check if it's HTML (common error case)
            if excel_response.content.startswith(b'<!DOCTYPE') or b'<html' in excel_response.content[:100]:
                print("   ⚠️  Downloaded file appears to be HTML, Excel export may not be available")
            return None
        
        # Save to temporary file
        filename = f"team_composition_{tournament_id}.xlsx"
        filepath = os.path.join('/tmp', filename)
        
        with open(filepath, 'wb') as f:
            f.write(excel_response.content)
        
        print(f"   ✅ Downloaded Excel file: {filepath}")
        return filepath
        
    except Exception as e:
        print(f"   ❌ Error downloading team composition Excel: {e}")
        return None

if __name__ == "__main__":
    # Set up Flask app context
    app = create_app()
    
    with app.app_context():
        success = test_team_tournament_breitler_jakob()
        
        if success:
            print("🎉 BREITLER, JAKOB TEAM TOURNAMENT TEST PASSED! ✅")
            sys.exit(0)
        else:
            print("❌ Breitler, Jakob team tournament test failed")
            sys.exit(1)
