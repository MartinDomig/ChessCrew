#!/usr/bin/env python3
"""
Individual Tournament Import Script

This script allows you to import a specific tournament from chess-results.com
by providing the tournament URL or ID.

Usage:
    python import_tournament.py https://s2.chess-results.com/tnr1152295.aspx
    python import_tournament.py 1152295
    python import_tournament.py --url https://s2.chess-results.com/tnr1152295.aspx
    python import_tournament.py --id 1152295
"""

import sys
import os
import argparse
import logging
import re
from datetime import datetime

# Add the backend directory to Python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def extract_tournament_id(url_or_id):
    """Extract tournament ID from URL or return the ID if already provided"""
    if url_or_id.isdigit():
        return url_or_id
    
    # Extract ID from chess-results.com URL
    match = re.search(r'tnr(\d+)', url_or_id)
    if match:
        return match.group(1)
    
    raise ValueError(f"Could not extract tournament ID from: {url_or_id}")

def is_team_tournament(crawler, tournament_url, tournament_id):
    """
    Auto-detect if tournament is a team tournament by checking for team composition links
    """
    try:
        logger.info(f"🔍 Auto-detecting tournament type for {tournament_id}...")
        
        # Get the main tournament page
        response = crawler.session.get(tournament_url)
        if response.status_code != 200:
            logger.warning(f"Could not access tournament page: {response.status_code}")
            return False
            
        # Look for team-related keywords and links
        page_content = response.text.lower()
        
        # Check for team composition or team-related links
        team_indicators = [
            'team composition',
            'teamzusammensetzung', 
            'team-composition',
            'mannschaft',
            'team captain',
            'captain:',
        ]
        
        # More specific team-related URL patterns
        team_url_patterns = [
            r'tnr\d+\.aspx.*art=1[^0-9]',  # Team composition with art=1 (not art=10, art=11, etc.)
            r'tnr\d+\.aspx.*art=20',       # Team results with round results
            r'teamcomposition',
            r'team.*composition'
        ]
        
        team_score = 0
        for indicator in team_indicators:
            if indicator in page_content:
                team_score += 1
                logger.debug(f"Found team indicator: {indicator}")
        
        # Check for team-specific URL patterns
        import re
        for pattern in team_url_patterns:
            if re.search(pattern, page_content):
                team_score += 2  # URL patterns are stronger indicators
                logger.debug(f"Found team URL pattern: {pattern}")
        
        # Also check if we can find team composition navigation specifically
        # Look for links that actually go to team composition (not just any art=1)
        if re.search(r'tnr\d+\.aspx.*art=1[^0-9]', page_content) or 'team composition' in page_content:
            logger.info(f"✅ Team tournament detected (score: {team_score}/7)")
            return True
        elif team_score >= 2:
            logger.info(f"✅ Team tournament likely detected (score: {team_score}/7)")
            return True
        else:
            logger.info(f"❌ Individual tournament detected (score: {team_score}/7)")
            return False
            
    except Exception as e:
        logger.warning(f"Error detecting tournament type: {e}")
        logger.info("🤷 Defaulting to individual tournament")
        return False

def import_single_tournament(tournament_id, force=False):
    """Import a single tournament by ID"""
    try:
        # Import here to avoid issues with Flask app context
        from app import create_app
        from chess_results_crawler import ChessResultsCrawler
        from db.models import Tournament, TournamentPlayer, Game, db
        
        # Create Flask app context
        app = create_app()
        
        with app.app_context():
            crawler = ChessResultsCrawler()
            
            # Build the tournament URL
            tournament_url = f"https://chess-results.com/tnr{tournament_id}.aspx"
            logger.info(f"Importing tournament: {tournament_url}")
            
            # Step 1: Check if tournament already imported
            existing_tournament = Tournament.query.filter_by(chess_results_id=tournament_id).first()
            if existing_tournament and not force:
                logger.warning(f"Tournament {tournament_id} already imported: {existing_tournament.name}")
                return {
                    'success': False,
                    'error': 'Tournament already imported',
                    'existing_tournament': existing_tournament.name
                }
            elif existing_tournament and force:
                logger.info(f"🗑️  Force mode: Removing existing tournament {tournament_id}: {existing_tournament.name}")
                # Delete associated games and players first
                TournamentPlayer.query.filter_by(tournament_id=existing_tournament.id).delete()
                Game.query.filter_by(tournament_id=existing_tournament.id).delete()
                db.session.delete(existing_tournament)
                db.session.commit()
                logger.info("✅ Existing tournament data removed")
            
            # Step 2: Login to chess-results.com
            if not crawler.login():
                logger.error("Failed to login to chess-results.com")
                return {'success': False, 'error': 'Failed to login to chess-results.com'}
            
            # Step 3: Get tournament details (this now includes ELO check)
            tournament_details = crawler.get_tournament_details(tournament_url, tournament_id)
            if not tournament_details:
                logger.error(f"Could not get details for tournament {tournament_id}")
                return {'success': False, 'error': 'Could not get tournament details'}
            
            tournament_name = tournament_details.get('name', f'Tournament {tournament_id}')
            logger.info(f"Tournament name: {tournament_name}")
            
            # Step 4: Download Excel export
            excel_file = crawler.download_excel_export(tournament_details)
            if not excel_file:
                logger.error(f"Could not download Excel file for tournament {tournament_id}")
                return {'success': False, 'error': 'Could not download Excel file'}
            
            logger.info(f"Downloaded Excel file: {excel_file}")
            
            # Step 5: Import tournament using the tournament_importer module
            try:
                result = crawler.import_tournament_from_excel_file(excel_file, tournament_name, tournament_id)
                
                # Clean up the temporary file
                if os.path.exists(excel_file):
                    os.remove(excel_file)
                
                return result
                
            except Exception as import_error:
                # Clean up the temporary file even if import fails
                if os.path.exists(excel_file):
                    os.remove(excel_file)
                raise import_error
                
    except Exception as e:
        logger.error(f"Error importing tournament {tournament_id}: {str(e)}", exc_info=True)
        return {'success': False, 'error': str(e)}

def import_team_tournament(tournament_id, force=False):
    """Import a team tournament using team composition with individual games"""
    try:
        from app import create_app
        from chess_results_crawler import ChessResultsCrawler
        from db.models import Tournament, TournamentPlayer, Game, db
        from tournament_importer import import_tournament_from_excel
        
        # Create Flask app context
        app = create_app()
        
        with app.app_context():
            crawler = ChessResultsCrawler()
            
            # Build the tournament URL
            tournament_url = f"https://chess-results.com/tnr{tournament_id}.aspx"
            logger.info(f"Importing team tournament: {tournament_url}")
            
            # Step 1: Check if tournament already imported
            existing_tournament = Tournament.query.filter_by(chess_results_id=tournament_id).first()
            if existing_tournament and not force:
                logger.warning(f"Tournament {tournament_id} already imported: {existing_tournament.name}")
                return {
                    'success': False,
                    'error': 'Tournament already imported',
                    'existing_tournament': existing_tournament.name
                }
            elif existing_tournament and force:
                logger.info(f"🗑️  Force mode: Removing existing tournament {tournament_id}: {existing_tournament.name}")
                # Delete associated games and players first
                TournamentPlayer.query.filter_by(tournament_id=existing_tournament.id).delete()
                Game.query.filter_by(tournament_id=existing_tournament.id).delete()
                db.session.delete(existing_tournament)
                db.session.commit()
                logger.info("✅ Existing tournament data removed")
            
            # Step 2: Login to chess-results.com
            if not crawler.login():
                logger.error("Failed to login to chess-results.com")
                return {'success': False, 'error': 'Failed to login to chess-results.com'}
            
            # Step 3: Get tournament details
            tournament_details = crawler.get_tournament_details(tournament_url, tournament_id)
            if not tournament_details:
                logger.error(f"Could not get details for tournament {tournament_id}")
                return {'success': False, 'error': 'Could not get tournament details'}
            
            tournament_name = tournament_details.get('name', f'Tournament {tournament_id}')
            logger.info(f"Team tournament name: {tournament_name}")
            
            # Step 4: Navigate to team composition page
            logger.info("🔍 Looking for team composition with round-results...")
            team_composition_url = crawler.get_team_composition_url(tournament_url, tournament_id)
            
            if not team_composition_url:
                logger.error("❌ Could not find team composition with round-results page!")
                return {'success': False, 'error': 'Could not find team composition page'}
            
            logger.info(f"✅ Found team composition page: {team_composition_url}")
            
            # Step 5: Download Excel export from team composition page
            logger.info("📊 Downloading team composition Excel export...")
            excel_file = crawler.download_team_composition_excel(team_composition_url, tournament_id)
            
            if not excel_file:
                logger.error("❌ Failed to download team composition Excel!")
                return {'success': False, 'error': 'Could not download team composition Excel'}
            
            logger.info(f"✅ Downloaded team composition Excel: {excel_file}")
            
            # Step 6: Import tournament using the tournament_importer module
            try:
                result = import_tournament_from_excel(
                    excel_file, tournament_name, 
                    date=datetime.now(),
                    chess_results_id=tournament_id
                )
                
                # Extract values from result dictionary
                ranked_players = result.get('ranked_players', [])
                game_count = result.get('imported_games', 0)
                mapped_players = result.get('mapped_players', 0)
                
                # Clean up the temporary file
                if os.path.exists(excel_file):
                    os.remove(excel_file)
                
                return {
                    'success': True,
                    'tournament_name': tournament_name,
                    'location': 'Unknown',
                    'date': datetime.now().strftime('%Y-%m-%d'),
                    'imported_players': len(ranked_players),
                    'imported_games': game_count,
                    'mapped_players': mapped_players
                }
                
            except Exception as import_error:
                # Clean up the temporary file even if import fails
                if os.path.exists(excel_file):
                    os.remove(excel_file)
                raise import_error
                
    except Exception as e:
        logger.error(f"Error importing team tournament {tournament_id}: {str(e)}", exc_info=True)
        return {'success': False, 'error': str(e)}

def main():
    parser = argparse.ArgumentParser(
        description='Import a specific tournament from chess-results.com',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s https://s2.chess-results.com/tnr1152295.aspx
  %(prog)s 1152295
  %(prog)s --url https://chess-results.com/tnr1152295.aspx
  %(prog)s --id 1152295
        """
    )
    
    # Positional argument (URL or ID)
    parser.add_argument('tournament', nargs='?', help='Tournament URL or ID')
    
    # Optional arguments
    parser.add_argument('--url', help='Tournament URL')
    parser.add_argument('--id', help='Tournament ID')
    parser.add_argument('--force', action='store_true', 
                       help='Force import even if tournament already exists')
    parser.add_argument('--team', action='store_true', 
                       help='Import as team tournament with individual games from Team Composition page')
    
    args = parser.parse_args()
    
    # Determine tournament ID from arguments
    tournament_input = args.tournament or args.url or args.id
    
    if not tournament_input:
        parser.error("No tournament URL or ID provided")
    
    try:
        tournament_id = extract_tournament_id(tournament_input)
        logger.info(f"Tournament ID: {tournament_id}")
        
        # Auto-detect tournament type unless explicitly specified
        tournament_url = f"https://chess-results.com/tnr{tournament_id}.aspx"
        
        if args.team:
            logger.info("🏁 Team tournament mode explicitly requested")
            is_team = True
        else:
            # Auto-detect tournament type
            from chess_results_crawler import ChessResultsCrawler
            crawler = ChessResultsCrawler()
            if not crawler.login():
                logger.error("Failed to login for tournament type detection")
                sys.exit(1)
            is_team = is_team_tournament(crawler, tournament_url, tournament_id)
        
        # Import the tournament using the appropriate method
        if is_team:
            logger.info("🏆 Importing as team tournament...")
            result = import_team_tournament(tournament_id, force=args.force)
        else:
            logger.info("👤 Importing as individual tournament...")
            result = import_single_tournament(tournament_id, force=args.force)
        
        if result and result.get('success'):
            logger.info(f"✓ Successfully imported tournament:")
            logger.info(f"  Name: {result.get('tournament_name')}")
            logger.info(f"  Location: {result.get('location')}")
            logger.info(f"  Date: {result.get('date')}")
            logger.info(f"  Players: {result.get('imported_players')}")
            logger.info(f"  Games: {result.get('imported_games')}")
            logger.info(f"  Mapped players: {result.get('mapped_players')}")
            logger.info("Import completed successfully!")
            sys.exit(0)
        else:
            error_msg = result.get('error', 'Unknown error') if result else 'No result returned'
            logger.error(f"✗ Failed to import tournament: {error_msg}")
            logger.error("Import failed!")
            sys.exit(1)
            
    except ValueError as e:
        logger.error(f"Invalid tournament input: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
