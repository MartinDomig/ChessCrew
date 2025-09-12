#!/bin/bash

# Email Processor Wrapper Script for Postfix
# This script sets up the virtual environment and runs the email processor

# Path to the virtual environment
VENV_PATH="/home/martin/chesscrew/venv"

# Path to the backend directory
BACKEND_DIR="/home/martin/chesscrew/backend"

# Activate the virtual environment
if [ -f "$VENV_PATH/bin/activate" ]; then
    source "$VENV_PATH/bin/activate"
else
    echo "Virtual environment not found at $VENV_PATH" >&2
    exit 1
fi

# Change to the backend directory
cd "$BACKEND_DIR" || {
    echo "Failed to change to directory $BACKEND_DIR" >&2
    exit 1
}

# Execute the Python script, passing through stdin
exec python email_processor.py
