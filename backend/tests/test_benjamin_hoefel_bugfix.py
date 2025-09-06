#!/usr/bin/env python3
"""
Test for Benjamin Hoefel Pkt./Wtg column detection bugfix

This test verifies that tournaments with explicit 'Pkt.' columns and Wtg1/Wtg2/Wtg3 columns
are imported correctly, with the actual tournament points from the 'Pkt.' column and tiebreaks
from the Wtg columns.

Specifically tests the fix for the issue where Benjamin Hoefel was imported with 45.5 points
(from Wtg1) instead of 5.5 points (from Pkt. column) in the Schach Tirol Open 2025.

Bug: Tournament 1107066 - Benjamin Hoefel showed 45.5 points instead of 5.5
Fix: Enhanced tournament_importer.py to detect Pkt./PKT. columns when no TB columns present
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

def create_test_excel_pkt_wtg():
    """
    Create a test Excel file that mimics the Schach Tirol Open 2025 format
    with 'Pkt.' and Wtg1/Wtg2/Wtg3 columns
    """
    # Create test data that mimics the problematic tournament structure
    data = [
        ['Aus der Turnierdatenbank von Chess-Results https://chess-results.com', None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None],
        ['Test Tournament with Pkt and Wtg columns', None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None],
        ['Die Seite wurde zuletzt aktualisiert am 30.08.2025 13:47:05', None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None],
        ['Endtabelle nach 9 Runden', None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None],
        ['Rg.', None, None, 'Name', 'Land', '1.Rd', '2.Rd', '3.Rd', '4.Rd', '5.Rd', '6.Rd', '7.Rd', '8.Rd', '9.Rd', 'Pkt.', 'Wtg1', 'Wtg2', 'Wtg3', 'Rp'],
        [1, None, None, 'Player One', 'GER', '14s1', '26w1', '20s1', '5w1', '3s1', '4s1', '2w0', '10w1', '8s1', 8.0, 47.0, 50.5, 1526, 1877],
        [2, None, None, 'Player Two', 'AUT', '11w1', '7s0', '21w1', '22s1', '9w1', '10s1', '1s1', '4w1', '3w0', 7.0, 47.5, 51.5, 1493, 1713],
        [7, None, None, 'Benjamin Hoefel Test', 'AUT', '27s1', '2w1', '4s½', '3w0', '6s0', '17w1', '22w1', '9s0', '12w1', 5.5, 45.5, 49.0, 1446, 1526],
        [8, None, None, 'Player Eight', 'AUT', '5s0', '28w1', '18s½', '26w½', '19s½', '13w1', '11s1', '16w+', '1w0', 5.5, 42.5, 46.0, 1439, 1482],
        [9, None, None, 'Player Nine', 'AUT', '37s1', '10s½', '12w0', '17w1', '2s0', '19w1', '26s1', '7w1', '4s0', 5.5, 42.0, 45.5, 1440, 1520],
    ]
    
    # Create DataFrame and save to temporary Excel file
    df = pd.DataFrame(data)
    temp_file = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
    df.to_excel(temp_file.name, index=False, header=False)
    return temp_file.name

def test_benjamin_hoefel_bugfix():
    """Test that Benjamin Hoefel tournament format is imported correctly"""
    
    print("🧪 Testing Benjamin Hoefel Pkt./Wtg column detection bugfix")
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
        
        # Test: Tournament with Pkt. and Wtg columns
        print("📋 Testing tournament with 'Pkt.' and Wtg columns")
        print("-" * 50)
        
        excel_file = create_test_excel_pkt_wtg()
        print(f"Created test Excel file: {excel_file}")
        
        result = import_tournament_from_excel(
            excel_file,
            "Test Schach Tirol Open Format",
            date=datetime(2025, 8, 30),
            chess_results_id="test_benjamin_hoefel"
        )
        
        if not result or not result.get('success', False):
            print(f"❌ Failed to import Pkt./Wtg format tournament! {result}")
            return False
        
        print("✅ Pkt./Wtg format tournament imported successfully")
        
        # Verify Benjamin Hoefel's data
        tournament = Tournament.query.filter_by(chess_results_id='test_benjamin_hoefel').first()
        if not tournament:
            print("❌ Pkt./Wtg format tournament not found in database!")
            return False
        
        benjamin = None
        players = TournamentPlayer.query.filter_by(tournament_id=tournament.id).all()
        for player in players:
            if 'Benjamin Hoefel' in player.name:
                benjamin = player
                break
        
        if not benjamin:
            print("❌ Benjamin Hoefel not found in Pkt./Wtg format tournament!")
            print("Available players:")
            for p in players:
                print(f"   {p.name}: {p.points} pts")
            return False
        
        print(f"✅ Found Benjamin Hoefel: {benjamin.name}")
        print(f"   Points: {benjamin.points}")
        print(f"   Tiebreak 1: {benjamin.tiebreak1}")
        print(f"   Tiebreak 2: {benjamin.tiebreak2}")
        
        # Validate the fix: points should be 5.5 (from Pkt. column), not 45.5 (from Wtg1 column)
        if benjamin.points != 5.5:
            print(f"❌ BUGFIX FAILED: Expected 5.5 points, got {benjamin.points}")
            print("   This indicates Wtg1 was used as points instead of Pkt. column")
            return False
        
        if benjamin.tiebreak1 != 45.5:
            print(f"❌ BUGFIX FAILED: Expected 45.5 tiebreak1, got {benjamin.tiebreak1}")
            print("   This indicates Wtg1 was not properly assigned as first tiebreak")
            return False
        
        if benjamin.tiebreak2 != 49.0:
            print(f"❌ BUGFIX FAILED: Expected 49.0 tiebreak2, got {benjamin.tiebreak2}")
            print("   This indicates Wtg2 was not properly assigned as second tiebreak")
            return False
        
        print("🎉 BENJAMIN HOEFEL BUGFIX VERIFIED!")
        print("   ✓ Points from 'Pkt.' column (5.5)")
        print("   ✓ First tiebreak from Wtg1 column (45.5)")
        print("   ✓ Second tiebreak from Wtg2 column (49.0)")
        print()
        
        # Cleanup temporary file
        os.unlink(excel_file)
        
        print("🎉 BENJAMIN HOEFEL TEST PASSED! ✅")
        print()
        print("📊 Summary:")
        print("   ✅ Pkt./Wtg format: Points from Pkt. column, tiebreaks from Wtg columns")
        print("   ✅ Bugfix verified: No more importing first tiebreak as tournament points")
        print("   ✅ Benjamin Hoefel scenario: 5.5 points (not 45.5) correctly imported")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_existing_formats_still_work():
    """Verify that existing formats still work after the Benjamin Hoefel fix"""
    
    print("🔍 Testing that existing formats still work...")
    print("-" * 50)
    
    try:
        # Clear database
        Game.query.delete()
        TournamentPlayer.query.delete() 
        Tournament.query.delete()
        db.session.commit()
        
        # Test TB-only format (should still work)
        data = [
            ['Test TB Only Format', None, None, None, None, None, None, None, None, None, None, None],
            ['Rk.', None, 'Name', 'Rtg', 'FED', '1', '2', '3', 'TB1', 'TB2', 'TB3'],
            [1, None, 'Legacy Player', 1500, 'AUT', '*', 1, 1, 2.0, 15.0, 0.0],
        ]
        
        df = pd.DataFrame(data)
        temp_file = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
        df.to_excel(temp_file.name, index=False, header=False)
        
        result = import_tournament_from_excel(
            temp_file.name,
            "Test TB Only Format After Benjamin Fix",
            date=datetime(2025, 9, 6),
            chess_results_id="test_tb_only_after_benjamin"
        )
        
        if result and result.get('success'):
            tournament = Tournament.query.filter_by(chess_results_id='test_tb_only_after_benjamin').first()
            if tournament:
                player = TournamentPlayer.query.filter_by(tournament_id=tournament.id).first()
                if player and player.points == 2.0 and player.tiebreak1 == 15.0:
                    print("✅ Legacy TB-only format still works correctly")
                    os.unlink(temp_file.name)
                    return True
        
        print("❌ Legacy TB-only format broken by Benjamin Hoefel fix")
        os.unlink(temp_file.name)
        return False
        
    except Exception as e:
        print(f"❌ Legacy format test failed: {e}")
        return False

if __name__ == "__main__":
    # Set up Flask app context
    app = create_app()
    
    with app.app_context():
        success1 = test_benjamin_hoefel_bugfix()
        success2 = test_existing_formats_still_work()
        
        if success1 and success2:
            print("🎉 ALL BENJAMIN HOEFEL TESTS PASSED! ✅")
            sys.exit(0)
        else:
            print("❌ Some tests failed")
            sys.exit(1)
