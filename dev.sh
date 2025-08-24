#!/bin/bash
set -e

# Create a Python virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Install the required Python packages
pip install -r backend/requirements.txt

export FLASK_SECRET_KEY="my secret key"

# Start the Flask development server
python -m backend.app

