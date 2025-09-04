#!/bin/bash
set -e

# Create a Python virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Install the required Python packages
pip install -r requirements.txt

export FLASK_SECRET_KEY="my secret key"
export FLASK_ENV=development

# Start the Flask development server
python -m app

