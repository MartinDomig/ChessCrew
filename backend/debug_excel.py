#!/usr/bin/env python3
"""Test script to debug crosstable Excel import"""

import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, '/home/martin/chesscrew/backend')

import pandas as pd
import glob
from tournament_importer import detect_round_columns, parse_players, parse_games
from db.models import Tournament
import tempfile

def debug_excel_import():
    """Debug the Excel import process"""
    
    # Find the most recently modified tournament Excel file
    pattern = '/tmp/tournament_*.xlsx'
    files = glob.glob(pattern)
    if not files:
        print('No tournament Excel files found')
        return
        
    latest_file = max(files, key=os.path.getmtime)
    print(f'Debugging file: {latest_file}')
    
    # Read the Excel file with header from row 4 (0-indexed)
    df = pd.read_excel(latest_file, header=4)
    print(f'Shape: {df.shape}')
    print(f'Headers: {list(df.columns)}')
    
    # Detect round columns
    header = list(df.columns)
    round_columns = detect_round_columns(header)
    print(f'Round columns detected: {round_columns}')
    
    # Print first few data rows
    print('\nFirst few data rows:')
    for i in range(min(3, len(df))):
        row_data = {}
        for col in header:
            row_data[col] = str(df.iloc[i][col]).strip()
        print(f'Row {i}: {row_data}')
        
        # Check round data specifically
        print(f'  Round data for row {i}:')
        for round_col in round_columns:
            round_result = row_data.get(round_col, '')
            print(f'    {round_col}: "{round_result}"')
            
            # Test the regex matching
            import re
            if round_result and round_result not in ['*', '***', '+', 'nan']:
                m = re.match(r'^(\d+)([wsb])([10½+])$', round_result)
                if m:
                    opponent_nr = int(m.group(1))
                    color = m.group(2)
                    result = m.group(3)
                    print(f'      -> Parsed: opponent={opponent_nr}, color={color}, result={result}')
                else:
                    print(f'      -> No regex match')
            else:
                print(f'      -> Empty or special value')

if __name__ == '__main__':
    debug_excel_import()
