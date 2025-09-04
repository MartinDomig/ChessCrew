#!/usr/bin/env python3
"""
Test utilities and path setup for backend tests
"""

import sys
import os

# Add the parent directory (backend) to Python path so tests can import modules
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
