#!/usr/bin/env python3

import sys
import os

# Add the parent directory to the path so we can import from the backend
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chess_results_crawler import ChessResultsCrawler

def test_club_championship_detection():
    """Test the club championship detection"""
    
    crawler = ChessResultsCrawler()
    
    print("🔍 Testing club championship detection...")
    
    # Login first
    if not crawler.login():
        print("❌ Failed to login")
        return
    
    # Test the specific tournament title that should be detected as unrated
    test_titles = [
        "Vereinsmeisterschaft 2024-2025 B-Gruppe",
        "12. Mödlinger Aktivschachturnier für Kinder bis 12 Jahre",
        "Club Championship A-Group",
        "Training Tournament",
        "Regular Tournament (should not be detected)"
    ]
    
    for title in test_titles:
        print(f"\n📝 Testing title: '{title}'")
        
        # Create a mock soup with h2 element
        from bs4 import BeautifulSoup
        mock_html = f"<html><h2>{title}</h2></html>"
        soup = BeautifulSoup(mock_html, 'html.parser')
        
        # Extract the logic from check_elo_calculation for testing
        tournament_title = soup.find('h2')
        if tournament_title:
            title_text = tournament_title.get_text().lower()
            
            # Use the same unrated indicators from our enhanced logic
            unrated_indicators = [
                # Children's tournaments
                r'kinder',  # German for children
                r'youth',  # English
                r'jugend',  # German for youth
                r'children',  # English
                r'bis\s+\d+\s+jahre',  # "bis 12 Jahre" = up to 12 years
                r'under\s+\d+',  # "Under 12"
                r'u\d+',  # "U12"
                
                # Club internal tournaments (typically unrated)
                r'vereinsmeisterschaft',  # German club championship
                r'club\s+championship',  # English club championship
                r'vereinsturnier',  # German club tournament
                r'internal\s+tournament',  # English internal tournament
                r'clubmeisterschaft',  # Alternative German spelling
                r'hausturnier',  # German house tournament
                r'\b[a-z]+\s*-\s*gruppe\b',  # "B-Gruppe", "A-Gruppe" etc.
                
                # Training/practice tournaments
                r'training',  # Training tournaments
                r'übung',  # German practice
                r'practice',  # English practice
                r'freundschaft',  # German friendly match
                r'friendly',  # English friendly
            ]
            
            detected = False
            detected_pattern = None
            
            import re
            for indicator in unrated_indicators:
                if re.search(indicator, title_text):
                    detected = True
                    detected_pattern = indicator
                    break
            
            if detected:
                print(f"   ✅ DETECTED as unrated - pattern: '{detected_pattern}'")
            else:
                print(f"   ❌ NOT detected as unrated")
        else:
            print(f"   ⚠️  No title found")

if __name__ == "__main__":
    test_club_championship_detection()
