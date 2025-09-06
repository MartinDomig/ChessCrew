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

def import_single_tournament(tournament_id):
    """Import a single tournament by ID"""
    try:
        # Import here to avoid issues with Flask app context
        from app import create_app
        from chess_results_crawler import ChessResultsCrawler
        
        # Create Flask app context
        app = create_app()
        
        with app.app_context():
            crawler = ChessResultsCrawler()
            
            # Build the tournament URL
            tournament_url = f"https://chess-results.com/tnr{tournament_id}.aspx"
            logger.info(f"Importing tournament: {tournament_url}")
            
            # Import the tournament
            result = crawler.import_tournament(tournament_url)
            
            if result and result.get('success'):
                logger.info(f"✓ Successfully imported tournament:")
                logger.info(f"  Name: {result.get('tournament_name')}")
                logger.info(f"  Location: {result.get('location')}")
                logger.info(f"  Date: {result.get('date')}")
                logger.info(f"  Players: {result.get('imported_players')}")
                logger.info(f"  Games: {result.get('imported_games')}")
                logger.info(f"  Mapped players: {result.get('mapped_players')}")
                return result
            else:
                logger.error(f"✗ Failed to import tournament: {result.get('error', 'Unknown error')}")
                return None
                
    except Exception as e:
        logger.error(f"Error importing tournament {tournament_id}: {str(e)}", exc_info=True)
        return None

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
    
    args = parser.parse_args()
    
    # Determine tournament ID from arguments
    tournament_input = args.tournament or args.url or args.id
    
    if not tournament_input:
        parser.error("No tournament URL or ID provided")
    
    try:
        tournament_id = extract_tournament_id(tournament_input)
        logger.info(f"Tournament ID: {tournament_id}")
        
        # Import the tournament
        result = import_single_tournament(tournament_id)
        
        if result:
            logger.info("Import completed successfully!")
            sys.exit(0)
        else:
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
