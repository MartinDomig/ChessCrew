#!/usr/bin/env python3
"""
Simple test script to verify the updated get_tournament_details method
"""

from chess_results_crawler import ChessResultsCrawler
import logging

# Set up logging to see what's happening
logging.basicConfig(level=logging.INFO)

def test_tournament_details():
    """Test the tournament details extraction"""
    crawler = ChessResultsCrawler()
    
    # Login first
    if not crawler.login():
        print("Failed to login")
        return False
    
    # Test with a sample tournament URL and ID
    # You can replace these with actual values for testing
    test_tournament_url = "https://chess-results.com/tnr123456.aspx"
    test_tournament_id = "123456"
    
    print(f"Testing tournament details extraction for ID: {test_tournament_id}")
    
    try:
        details = crawler.get_tournament_details(test_tournament_url, test_tournament_id)
        
        if details:
            print("Tournament details extracted successfully!")
            print(f"Tournament ID: {details.get('tournament_id')}")
            print(f"Tournament Name: {details.get('name')}")
            print(f"Has ELO Calculation: {details.get('has_elo_calculation')}")
            
            metadata = details.get('metadata', {})
            print("\nMetadata:")
            for key, value in metadata.items():
                if value:
                    print(f"  {key}: {value}")
                    
            return True
        else:
            print("No tournament details found")
            return False
            
    except Exception as e:
        print(f"Error testing tournament details: {e}")
        return False

if __name__ == "__main__":
    test_tournament_details()
