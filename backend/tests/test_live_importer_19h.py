#!/usr/bin/env python3
"""
Test script for the live importer that would run at 19:00 (7 PM) daily
This script simulates the evening automated tournament import process.
"""

import sys
import os
import logging
from datetime import datetime, time

# Add the backend directory to Python path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

# Set up logging
log_file = os.path.join(backend_dir, 'logs', 'live_importer_19h.log')
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

def run_evening_import():
    """Main function for evening 19:00 import process"""
    current_time = datetime.now()
    
    logger.info("=" * 60)
    logger.info(f"🌅 EVENING LIVE IMPORTER TEST - Started at {current_time}")
    logger.info(f"⏰ Simulating 19:00 daily automated import process")
    logger.info("=" * 60)
    
    try:
        # Import Flask app and crawler
        from app import create_app
        from chess_results_crawler import run_crawler
        
        # Create Flask app context
        app = create_app()
        
        logger.info("🔧 Flask app context created")
        
        with app.app_context():
            logger.info("🚀 Starting automated tournament crawling...")
            
            # Run the live crawler to check for new/updated tournaments
            processed_count = run_crawler()
            
            logger.info(f"✅ Live import completed successfully!")
            logger.info(f"📊 Total tournaments processed: {processed_count}")
            
            # Evening specific summary
            if processed_count > 0:
                logger.info(f"🎯 Evening import successful - {processed_count} tournaments updated")
            else:
                logger.info("📋 No new tournaments found - database is up to date")
                
    except Exception as e:
        logger.error(f"❌ Error in evening live import: {str(e)}", exc_info=True)
        return False
    
    finally:
        end_time = datetime.now()
        duration = end_time - current_time
        logger.info(f"⏱️  Total processing time: {duration.total_seconds():.2f} seconds")
        logger.info(f"🏁 Evening live importer finished at {end_time}")
        logger.info("=" * 60)
    
    return True

def check_system_status():
    """Check if the system is ready for live imports"""
    logger.info("🔍 Checking system status for live imports...")
    
    try:
        # Check database connection
        from app import create_app
        from db.models import db, Tournament
        
        app = create_app()
        with app.app_context():
            # Test database connection
            tournament_count = Tournament.query.count()
            logger.info(f"📊 Database connection OK - {tournament_count} tournaments in database")
            
        # Check for required environment variables
        required_vars = ['FLASK_SECRET_KEY']
        missing_vars = []
        
        for var in required_vars:
            if not os.environ.get(var):
                missing_vars.append(var)
        
        if missing_vars:
            logger.warning(f"⚠️  Missing environment variables: {missing_vars}")
            logger.info("Setting default values for testing...")
            os.environ['FLASK_SECRET_KEY'] = 'test-secret-key-for-live-import'
        
        logger.info("✅ System status check completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ System status check failed: {str(e)}")
        return False

def main():
    """Main test function"""
    logger.info("🔄 Starting live importer test for 19:00 daily schedule")
    
    # Check system status first
    if not check_system_status():
        logger.error("❌ System status check failed - aborting test")
        sys.exit(1)
    
    # Run the evening import process
    success = run_evening_import()
    
    if success:
        logger.info("🎉 Live importer test completed successfully!")
        logger.info("💡 This script can be scheduled to run daily at 19:00 with:")
        logger.info("   crontab -e")
        logger.info("   0 19 * * * /home/martin/chesscrew/backend/test_live_importer_19h.py")
        sys.exit(0)
    else:
        logger.error("❌ Live importer test failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
