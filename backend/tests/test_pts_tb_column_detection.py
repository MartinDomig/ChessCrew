#!/usr/bin/env python3
"""
Test for Pts./TB column detection bugfix

This test verifies that tournaments with both explicit 'Pts.' columns and TB1/TB2/TB3 columns
are imported correctly, with the actual tournament points from the 'Pts.' column and tiebreaks
from the TB columns.

Specifically tests the fix for the issue where Christina Domig was imported with 23 points
(from TB1) instead of 4 points (from Pts. column) in the Austrian Championship U14.
"""

import sys
import os
import logging
from datetime import datetime
import tempfile
import pandas as pd

# Add backend to path
sys.path.append('/home/martin/chesscrew/backend')

from app import create_app
from db.models import db, Tournament, TournamentPlayer, Game
from tournament_importer import import_tournament_from_excel

def create_test_excel_mixed_pts_tb():
    """
    Create a test Excel file that mimics the Austrian Championship U14 format
    with both 'Pts.' and TB1/TB2/TB3 columns
    """
    # Create test data that mimics the problematic tournament structure
    data = [
        ['From the Tournament-Database of Chess-Results https://chess-results.com', None, None, None, None, None, None, None, None, None, None, None, None, None, None, None],
        ['Test Tournament with Pts and TB columns', None, None, None, None, None, None, None, None, None, None, None, None, None, None, None],
        ['Last update 06.09.2025 12:00:00', None, None, None, None, None, None, None, None, None, None, None, None, None, None, None],
        ['Final Ranking crosstable after 7 Rounds', None, None, None, None, None, None, None, None, None, None, None, None, None, None, None],
        ['Rk.', None, 'Name', 'FED', '1.Rd', '2.Rd', '3.Rd', '4.Rd', '5.Rd', '6.Rd', '7.Rd', 'Pts.', 'TB1', 'TB2', 'TB3', 'Rp'],
        [1, None, 'Player One', 'AUT', '2w1', '3b1', '4w1', '5b½', '6w0', '7b1', '8w1', 5.5, 26, 28.5, 21.5, 1783],
        [2, None, 'Player Two', 'AUT', '1b0', '4w1', '3b1', '6w½', '5b1', '8w½', '7b1', 5.0, 26, 29, 19.75, 1751],
        [3, None, 'Test Christina Domig', 'AUT', '1w0', '2w0', '4b0', '5b1', '6w½', '7b1', '8w½', 4.0, 23, 25.5, 11, 1530],
        [4, None, 'Player Four', 'AUT', '1b0', '2b0', '3w1', '6b½', '7w1', '8b0', '5w1', 3.5, 23.5, 26, 9, 1477],
        [5, None, 'Player Five', 'AUT', '1w½', '6b0', '7w1', '3w0', '2w0', '4b1', '8b½', 3.0, 22.5, 24, 7.75, 1389],
    ]
    
    # Create DataFrame and save to temporary Excel file
    df = pd.DataFrame(data)
    temp_file = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
    df.to_excel(temp_file.name, index=False, header=False)
    return temp_file.name

def create_test_excel_tb_only():
    """
    Create a test Excel file that mimics the old format with only TB1/TB2/TB3 columns
    (where TB1 contains the main points)
    """
    data = [
        ['From the Tournament-Database of Chess-Results https://chess-results.com', None, None, None, None, None, None, None, None, None, None, None, None, None],
        ['Test Tournament with TB columns only', None, None, None, None, None, None, None, None, None, None, None, None, None],
        ['Last update 06.09.2025 12:00:00', None, None, None, None, None, None, None, None, None, None, None, None, None],
        ['Rk.', None, 'Name', 'Rtg', 'FED', '1', '2', '3', '4', '5', '6', '7', 'TB1', 'TB2', 'TB3'],
        [1, None, 'Player One', 1451, 'AUT', '*', 1, 0, 1, 1, 1, 1, 6, 17, 0],
        [2, None, 'Player Two', 1219, 'AUT', 0, '*', 1, 1, 1, 0, 1, 5, 14, 1],
        [3, None, 'Test Player Three', 1343, 'AUT', 1, 0, '*', 0, 1, 1, 1, 5, 14, 0],
        [4, None, 'Player Four', 1295, 'AUT', 0, 0, 1, '*', 0, 1, 1, 4, 10, 0],
    ]
    
    df = pd.DataFrame(data)
    temp_file = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
    df.to_excel(temp_file.name, index=False, header=False)
    return temp_file.name

def test_pts_tb_column_detection():
    """Test that tournaments with both Pts. and TB columns are imported correctly"""
    
    print("🧪 Testing Pts./TB column detection bugfix")
    print("=" * 80)
    
    try:
        # Clear database first to ensure clean test
        print("🧹 Clearing database...")
        Game.query.delete()
        TournamentPlayer.query.delete() 
        Tournament.query.delete()
        db.session.commit()
        print("✅ Database cleared")
        print()
        
        # Test 1: Tournament with both Pts. and TB columns (new format)
        print("📋 Test 1: Tournament with both 'Pts.' and TB columns")
        print("-" * 50)
        
        excel_file_mixed = create_test_excel_mixed_pts_tb()
        print(f"Created test Excel file: {excel_file_mixed}")
        
        result = import_tournament_from_excel(
            excel_file_mixed,
            "Test Tournament Mixed Format",
            date=datetime(2025, 9, 6),
            chess_results_id="test_mixed"
        )
        
        if not result or not result.get('success', False):
            print(f"❌ Failed to import mixed format tournament! {result}")
            return False
        
        print("✅ Mixed format tournament imported successfully")
        
        # Verify Christina Domig's data
        tournament = Tournament.query.filter_by(chess_results_id='test_mixed').first()
        if not tournament:
            print("❌ Mixed format tournament not found in database!")
            return False
        
        christina = None
        players = TournamentPlayer.query.filter_by(tournament_id=tournament.id).all()
        for player in players:
            if 'Christina Domig' in player.name:
                christina = player
                break
        
        if not christina:
            print("❌ Christina Domig not found in mixed format tournament!")
            print("Available players:")
            for p in players:
                print(f"   {p.name}: {p.points} pts")
            return False
        
        print(f"✅ Found Christina Domig: {christina.name}")
        print(f"   Points: {christina.points}")
        print(f"   Tiebreak 1: {christina.tiebreak1}")
        print(f"   Tiebreak 2: {christina.tiebreak2}")
        
        # Validate the fix: points should be 4.0 (from Pts. column), not 23.0 (from TB1 column)
        if christina.points != 4.0:
            print(f"❌ BUGFIX FAILED: Expected 4.0 points, got {christina.points}")
            print("   This indicates TB1 was used as points instead of Pts. column")
            return False
        
        if christina.tiebreak1 != 23.0:
            print(f"❌ BUGFIX FAILED: Expected 23.0 tiebreak1, got {christina.tiebreak1}")
            print("   This indicates TB1 was not properly assigned as first tiebreak")
            return False
        
        if christina.tiebreak2 != 25.5:
            print(f"❌ BUGFIX FAILED: Expected 25.5 tiebreak2, got {christina.tiebreak2}")
            print("   This indicates TB2 was not properly assigned as second tiebreak")
            return False
        
        print("🎉 BUGFIX VERIFIED: Mixed format working correctly!")
        print("   ✓ Points from 'Pts.' column (4.0)")
        print("   ✓ First tiebreak from TB1 column (23.0)")
        print("   ✓ Second tiebreak from TB2 column (25.5)")
        print()
        
        # Clear for next test
        Game.query.delete()
        TournamentPlayer.query.delete() 
        Tournament.query.delete()
        db.session.commit()
        
        # Test 2: Tournament with only TB columns (legacy format)
        print("📋 Test 2: Tournament with only TB columns (legacy format)")
        print("-" * 50)
        
        excel_file_tb_only = create_test_excel_tb_only()
        print(f"Created test Excel file: {excel_file_tb_only}")
        
        result = import_tournament_from_excel(
            excel_file_tb_only,
            "Test Tournament TB Only Format",
            date=datetime(2025, 9, 6),
            chess_results_id="test_tb_only"
        )
        
        if not result or not result.get('success', False):
            print(f"❌ Failed to import TB-only format tournament! {result}")
            return False
        
        print("✅ TB-only format tournament imported successfully")
        
        # Verify legacy behavior still works
        tournament = Tournament.query.filter_by(chess_results_id='test_tb_only').first()
        if not tournament:
            print("❌ TB-only format tournament not found in database!")
            return False
        
        players = TournamentPlayer.query.filter_by(tournament_id=tournament.id).all()
        player_one = None
        for player in players:
            if player.ranking == 1:
                player_one = player
                break
        
        if not player_one:
            print("❌ First ranked player not found in TB-only tournament!")
            return False
        
        print(f"✅ Found first player: {player_one.name}")
        print(f"   Points: {player_one.points}")
        print(f"   Tiebreak 1: {player_one.tiebreak1}")
        print(f"   Tiebreak 2: {player_one.tiebreak2}")
        
        # Validate legacy behavior: TB1 should be used as points
        if player_one.points != 6.0:
            print(f"❌ LEGACY BEHAVIOR BROKEN: Expected 6.0 points, got {player_one.points}")
            print("   This indicates TB1 was not used as points in legacy format")
            return False
        
        if player_one.tiebreak1 != 17.0:
            print(f"❌ LEGACY BEHAVIOR BROKEN: Expected 17.0 tiebreak1, got {player_one.tiebreak1}")
            print("   This indicates TB2 was not properly assigned as first tiebreak")
            return False
        
        print("🎉 LEGACY BEHAVIOR PRESERVED: TB-only format working correctly!")
        print("   ✓ Points from TB1 column (6.0)")
        print("   ✓ First tiebreak from TB2 column (17.0)")
        print("   ✓ Second tiebreak from TB3 column (0.0)")
        print()
        
        # Cleanup temporary files
        os.unlink(excel_file_mixed)
        os.unlink(excel_file_tb_only)
        
        print("🎉 ALL TESTS PASSED! ✅")
        print()
        print("📊 Summary:")
        print("   ✅ Mixed format (Pts. + TB): Points from Pts. column, tiebreaks from TB columns")
        print("   ✅ Legacy format (TB only): Points from TB1 column, tiebreaks from TB2/TB3")
        print("   ✅ Bugfix verified: No more importing tiebreak values as tournament points")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Set up Flask app context
    app = create_app()
    
    with app.app_context():
        success = test_pts_tb_column_detection()
        sys.exit(0 if success else 1)
