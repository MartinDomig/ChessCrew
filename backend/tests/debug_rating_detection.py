#!/usr/bin/env python3

import sys
import os
import requests
from bs4 import BeautifulSoup
import re

# Add the parent directory to the path so we can import from the backend
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chess_results_crawler import ChessResultsCrawler

def debug_tournament_page(tournament_id):
    """Debug the tournament page to see rating calculation info"""
    crawler = ChessResultsCrawler()
    
    print(f"🔍 Debugging tournament {tournament_id} rating detection...")
    
    # Login first
    if not crawler.login():
        print("❌ Failed to login")
        return
    
    # Get tournament URL
    tournament_url = f"https://chess-results.com/tnr{tournament_id}.aspx"
    print(f"📄 Fetching: {tournament_url}")
    
    try:
        response = crawler.session.get(tournament_url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Save the page for manual inspection
        with open(f'/tmp/tournament_{tournament_id}_debug.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        print(f"💾 Saved page content to /tmp/tournament_{tournament_id}_debug.html")
        
        # Look for any text containing rating/elo keywords
        rating_keywords = ['rating', 'elo', 'rechnung', 'calculation', 'berechnung']
        
        print("\n🔎 Searching for rating-related text...")
        for keyword in rating_keywords:
            elements = soup.find_all(text=re.compile(keyword, re.IGNORECASE))
            for element in elements:
                text = element.strip()
                if text:
                    parent = element.parent
                    parent_text = parent.get_text().strip() if parent else ""
                    print(f"  📝 Found '{keyword}' in: '{text}'")
                    print(f"     Parent element: <{parent.name if parent else 'None'}> '{parent_text}'")
                    print()
        
        # Also search for common patterns
        print("🔍 Looking for common rating patterns...")
        patterns = [
            r'rating\s*calculation',
            r'elo\s*rechnung',
            r'berechnung',
            r'calculated',
            r'berechnet'
        ]
        
        page_text = response.text.lower()
        for pattern in patterns:
            matches = re.finditer(pattern, page_text)
            for match in matches:
                start = max(0, match.start() - 50)
                end = min(len(page_text), match.end() + 50)
                context = page_text[start:end]
                print(f"  🎯 Pattern '{pattern}': ...{context}...")
                print()
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    # Debug the problematic children's tournament
    debug_tournament_page("1221040")
