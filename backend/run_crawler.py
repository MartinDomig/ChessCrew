#!/usr/bin/env python3
"""
Scheduled script to crawl chess-results.com for finished tournaments
This script should be run via cron job on your VPS

IMPORTANT: This script should be run from within the virtual environment
or via the crawler_cron.sh wrapper script that activates the venv.
"""

import sys
import os
import logging
from datetime import datetime

# Add the backend directory to Python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

# Set up logging for cron job
log_file = os.path.join(backend_dir, 'logs', 'crawler.log')
os.makedirs(os.path.dirname(log_file), exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Main function for scheduled execution"""
    logger.info("=" * 50)
    logger.info(f"Starting scheduled crawler run at {datetime.now()}")
    
    try:
        # Import here to avoid issues with Flask app context
        from app import create_app
        from chess_results_crawler import run_crawler
        
        # Create Flask app context
        app = create_app()
        
        with app.app_context():
            # Run the crawler
            processed_count = run_crawler()
            logger.info(f"Crawler completed successfully. Processed {processed_count} tournaments")
            
    except Exception as e:
        logger.error(f"Error in scheduled crawler run: {str(e)}", exc_info=True)
        sys.exit(1)
    
    logger.info(f"Scheduled crawler run completed at {datetime.now()}")
    logger.info("=" * 50)

if __name__ == "__main__":
    main()
