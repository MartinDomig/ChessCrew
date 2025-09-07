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
import hashlib
import logging
import re
from datetime import datetime
from tournament_importer import import_tournament_from_excel
from db.models import db, Tournament, TournamentPlayer, Player

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

def import_tournament_from_excel_file(self, filepath, tournament_details):
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
            logger.info(f"Tournament {tournament_details['name']} already imported (checksum match)")
            return {'success': False, 'reason': 'already_imported'}

        tournament_details['checksum'] = checksum

        # Use the tournament_importer module
        result = import_tournament_from_excel(filepath=filepath, tournament_details=tournament_details)

        logger.info(f"Successfully imported tournament {tournament_id}: {result['tournament_name']}")
        logger.info(f"  Imported {result['imported_players']} players, {result['imported_games']} games")
        
        return result
        
    except Exception as e:
        logger.error(f"Error importing tournament {tournament_id}: {str(e)}")
        return {'success': False, 'reason': str(e)}


def import_tournament(crawler, tournament_id, force=False):
    """Import tournament by ID"""
    try:
        # Import here to avoid issues with Flask app context
        from app import create_app
        from db.models import Tournament, TournamentPlayer, Game, db
        
        # Create Flask app context
        app = create_app()
        
        with app.app_context():
            # Build the tournament URL
            tournament_url = f"https://chess-results.com/tnr{tournament_id}.aspx"
            logger.info(f"Reading tournament details from: {tournament_url}")

            # Get tournament details
            tournament_details = crawler.get_tournament_details(tournament_url, tournament_id)
            if not tournament_details:
                logger.error(f"Could not get details for tournament {tournament_id}")
                return {'success': False, 'error': 'Could not get tournament details'}
                        
            # Download Excel export
            excel_file = crawler.download_excel_export(tournament_details)

            if not excel_file:
                logger.error(f"Could not download Excel file for tournament {tournament_id}")
                return {'success': False, 'error': 'Could not download Excel file'}
            
            logger.info(f"Downloaded Excel file: {excel_file}")

            # write tournament details json file next to excel file
            import json
            details_file = excel_file.replace('.xlsx', '_details.json')
            with open(details_file, 'w', encoding='utf-8') as f:
                json.dump(tournament_details, f, ensure_ascii=False, indent=4)
            logger.info(f"Wrote tournament details to: {details_file}")
            
            # Convert date string to Python date object if needed
            if 'date' in tournament_details and isinstance(tournament_details['date'], str):
                try:
                    from datetime import datetime
                    tournament_details['date'] = datetime.strptime(tournament_details['date'], '%Y-%m-%d').date()
                except ValueError as e:
                    logger.warning(f"Could not parse date '{tournament_details['date']}': {e}")
                    tournament_details['date'] = None
            
            # Import tournament using the tournament_importer module
            try:
                result = import_tournament_from_excel(excel_file, tournament_details)
                
                # Clean up the temporary file
                # if os.path.exists(excel_file):
                #    os.remove(excel_file)
                
                return result
                
            except Exception as import_error:
                # Clean up the temporary file even if import fails
                # if os.path.exists(excel_file):
                #    os.remove(excel_file)
                raise import_error
                
    except Exception as e:
        logger.error(f"Error importing tournament {tournament_id}: {str(e)}", exc_info=True)
        return {'success': False, 'error': str(e)}

def main():
    from chess_results_crawler import ChessResultsCrawler

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
    
    args = parser.parse_args()
    
    # Determine tournament ID from arguments
    tournament_input = args.tournament or args.url or args.id
    
    if not tournament_input:
        parser.error("No tournament URL or ID provided")
    
    try:
        tournament_id = extract_tournament_id(tournament_input)
        logger.info(f"Tournament ID: {tournament_id}")
        
        crawler = ChessResultsCrawler()
        if not crawler.login():
            logger.error("Failed to login for tournament type detection")
            sys.exit(1)
        
        import_tournament(crawler, tournament_id, force=args.force)
        logger.info("Tournament import completed successfully")
        sys.exit(0)
        
    except ValueError as e:
        logger.error(f"Invalid tournament input: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
