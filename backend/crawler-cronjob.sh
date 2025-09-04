#!/bin/bash

source venv/bin/activate
export FLASK_SECRET_KEY=cronjob-importer
python run_crawler.py
