#!/bin/bash
# Production wrapper script for daily 19:00 tournament import
# This script activates the virtual environment and runs the live importer

# Activate virtual environment
source venv/bin/activate

# Set required environment variables
export FLASK_SECRET_KEY="my secret key"

# Run the live importer
python test_live_importer_19h.py

# Exit with the same code as the importer
exit $?
