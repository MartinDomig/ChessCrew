#!/bin/bash
"""
Wrapper script to run the tournament import script with proper environment setup.

This script ensures the virtual environment is activated before running the import.
"""

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR"
VENV_DIR="$BACKEND_DIR/venv"

# Check if virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    echo "Error: Virtual environment not found at $VENV_DIR"
    echo "Please run setup_crawler.sh first to create the virtual environment"
    exit 1
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Check if required environment variables are set
if [ -z "$FLASK_SECRET_KEY" ]; then
    echo "Warning: FLASK_SECRET_KEY environment variable not set"
    echo "Setting a default value for this session"
    export FLASK_SECRET_KEY="dev-secret-key-for-import"
fi

# Run the import script with all provided arguments
python "$BACKEND_DIR/import_tournament.py" "$@"
