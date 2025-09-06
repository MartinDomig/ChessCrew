#!/usr/bin/env python3
"""
Comprehensive column detection bugfix test

This test covers all the column detection issues that have been fixed:
1. Christina Domig issue: Pts. + TB1/TB2/TB3 columns
2. Benjamin Hoefel issue: Pkt. + Wtg1/Wtg2/Wtg3 columns
3. Legacy format: TB1/TB2/TB3 only
4. Standard format: Pts/Points patterns

This ensures all tournament formats are correctly imported.
"""

import sys
import os
import tempfile
import pandas as pd
from datetime import datetime

# Add backend to path
sys.path.append('/home/martin/chesscrew/backend')

from app import create_app
from db.models import db, Tournament, TournamentPlayer, Game
from tournament_importer import import_tournament_from_excel

def create_test_scenarios():
    """Create test data for all known column format scenarios"""
    
    scenarios = {}
    
    # Scenario 1: Christina Domig format (Pts. + TB1/TB2/TB3)
    scenarios['christina_domig'] = {
        'name': 'Christina Domig Format (Pts. + TB1/TB2/TB3)',
        'data': [
            ['Test Tournament Christina Format', None, None, None, None, None, None, None, None, None, None, None, None, None, None, None],
            ['Rk.', None, 'Name', 'FED', '1.Rd', '2.Rd', '3.Rd', '4.Rd', '5.Rd', '6.Rd', '7.Rd', 'Pts.', 'TB1', 'TB2', 'TB3', 'Rp'],
            [7, None, 'Christina Domig Test', 'AUT', '3w0', '-1', '4b0', '13b1', '14w½', '12b1', '6w½', 4.0, 23.0, 25.5, 11.0, 1530],
        ],
        'expected_points': 4.0,
        'expected_tb1': 23.0,
        'expected_tb2': 25.5,
        'player_name': 'Christina Domig Test'
    }
    
    # Scenario 2: Benjamin Hoefel format (Pkt. + Wtg1/Wtg2/Wtg3)
    scenarios['benjamin_hoefel'] = {
        'name': 'Benjamin Hoefel Format (Pkt. + Wtg1/Wtg2/Wtg3)',
        'data': [
            ['Test Tournament Benjamin Format', None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None],
            ['Rg.', None, None, 'Name', 'Land', '1.Rd', '2.Rd', '3.Rd', '4.Rd', '5.Rd', '6.Rd', '7.Rd', '8.Rd', '9.Rd', 'Pkt.', 'Wtg1', 'Wtg2', 'Wtg3', 'Rp'],
            [7, None, None, 'Benjamin Hoefel Test', 'AUT', '27s1', '2w1', '4s½', '3w0', '6s0', '17w1', '22w1', '9s0', '12w1', 5.5, 45.5, 49.0, 1446, 1526],
        ],
        'expected_points': 5.5,
        'expected_tb1': 45.5,
        'expected_tb2': 49.0,
        'player_name': 'Benjamin Hoefel Test'
    }
    
    # Scenario 3: Legacy format (TB1/TB2/TB3 only, TB1 = points)
    scenarios['legacy_tb'] = {
        'name': 'Legacy Format (TB1/TB2/TB3 only)',
        'data': [
            ['Test Tournament Legacy Format', None, None, None, None, None, None, None, None, None, None, None],
            ['Rk.', None, 'Name', 'Rtg', 'FED', '1', '2', '3', 'TB1', 'TB2', 'TB3'],
            [1, None, 'Legacy Player Test', 1500, 'AUT', '*', 1, 1, 2.5, 15.0, 0.0],
        ],
        'expected_points': 2.5,
        'expected_tb1': 15.0,
        'expected_tb2': 0.0,
        'player_name': 'Legacy Player Test'
    }
    
    # Scenario 4: Standard points format (Points/Pts pattern)
    scenarios['standard_points'] = {
        'name': 'Standard Points Format',
        'data': [
            ['Test Tournament Standard Format', None, None, None, None, None, None, None, None, None, None, None],
            ['Rank', None, 'Name', 'Country', '1', '2', '3', 'Points', 'Buchholz', 'Sonneborn'],
            [1, None, 'Standard Player Test', 'AUT', '2w1', '3b1', '4w½', 2.5, 12.0, 8.5],
        ],
        'expected_points': 2.5,
        'expected_tb1': 12.0,
        'expected_tb2': 8.5,
        'player_name': 'Standard Player Test'
    }
    
    return scenarios

def run_scenario_test(scenario_name, scenario_data):
    """Run a test for a specific column format scenario"""
    
    print(f"🔍 Testing: {scenario_data['name']}")
    print("-" * 60)
    
    try:
        # Clear database
        Game.query.delete()
        TournamentPlayer.query.delete()
        Tournament.query.delete()
        db.session.commit()
        
        # Create Excel file
        df = pd.DataFrame(scenario_data['data'])
        temp_file = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
        df.to_excel(temp_file.name, index=False, header=False)
        
        # Import tournament
        result = import_tournament_from_excel(
            temp_file.name,
            f"Test {scenario_name}",
            date=datetime(2025, 9, 6),
            chess_results_id=f"test_{scenario_name}"
        )
        
        success = False
        
        if result and result.get('success'):
            # Find the test player
            tournament = Tournament.query.filter_by(chess_results_id=f"test_{scenario_name}").first()
            if tournament:
                players = TournamentPlayer.query.filter_by(tournament_id=tournament.id).all()
                test_player = None
                for player in players:
                    if scenario_data['player_name'] in player.name:
                        test_player = player
                        break
                
                if test_player:
                    print(f"✅ Found player: {test_player.name}")
                    print(f"   Points: {test_player.points} (expected {scenario_data['expected_points']})")
                    print(f"   Tiebreak 1: {test_player.tiebreak1} (expected {scenario_data['expected_tb1']})")
                    print(f"   Tiebreak 2: {test_player.tiebreak2} (expected {scenario_data['expected_tb2']})")
                    
                    # Validate results
                    if (test_player.points == scenario_data['expected_points'] and 
                        test_player.tiebreak1 == scenario_data['expected_tb1'] and
                        test_player.tiebreak2 == scenario_data['expected_tb2']):
                        print(f"🎉 {scenario_data['name']} - PASSED ✅")
                        success = True
                    else:
                        print(f"❌ {scenario_data['name']} - VALUES MISMATCH")
                else:
                    print(f"❌ {scenario_data['name']} - PLAYER NOT FOUND")
            else:
                print(f"❌ {scenario_data['name']} - TOURNAMENT NOT FOUND")
        else:
            print(f"❌ {scenario_data['name']} - IMPORT FAILED: {result}")
        
        # Cleanup
        os.unlink(temp_file.name)
        print()
        
        return success
        
    except Exception as e:
        print(f"❌ {scenario_data['name']} - ERROR: {e}")
        print()
        return False

def test_comprehensive_column_detection():
    """Run comprehensive tests for all column detection scenarios"""
    
    print("🧪 Comprehensive Column Detection Bugfix Test")
    print("=" * 80)
    print("Testing all known tournament column format scenarios...")
    print()
    
    scenarios = create_test_scenarios()
    
    total_tests = len(scenarios)
    passed_tests = 0
    
    for scenario_name, scenario_data in scenarios.items():
        if run_scenario_test(scenario_name, scenario_data):
            passed_tests += 1
    
    print("📊 Comprehensive Test Results")
    print("=" * 40)
    print(f"Total scenarios tested: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print()
    
    if passed_tests == total_tests:
        print("🎉 ALL COMPREHENSIVE TESTS PASSED! ✅")
        print()
        print("✅ Christina Domig scenario (Pts. + TB1/TB2/TB3) - Fixed")
        print("✅ Benjamin Hoefel scenario (Pkt. + Wtg1/Wtg2/Wtg3) - Fixed") 
        print("✅ Legacy format (TB1/TB2/TB3 only) - Still working")
        print("✅ Standard format (Points/Pts patterns) - Still working")
        print()
        print("🔧 All column detection bugs have been successfully fixed!")
        return True
    else:
        print(f"❌ {total_tests - passed_tests} test(s) failed")
        print("Some column detection issues may still exist")
        return False

if __name__ == "__main__":
    # Set up Flask app context
    os.environ['FLASK_SECRET_KEY'] = 'test-secret-key'
    app = create_app()
    
    with app.app_context():
        success = test_comprehensive_column_detection()
        sys.exit(0 if success else 1)
