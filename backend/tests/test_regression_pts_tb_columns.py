#!/usr/bin/env python3
"""
Regression test for Pts./TB column detection bug

This test can be run as part of the test suite to ensure the bugfix remains working.
It tests the specific issue where tournaments with both 'Pts.' and TB1/TB2/TB3 columns
were incorrectly importing tiebreak values as tournament points.

Bug: https://github.com/your-repo/chesscrew/issues/XXX
Fix: Modified tournament_importer.py to detect explicit points columns when TB columns are present
"""

import unittest
import tempfile
import os
from datetime import datetime
import pandas as pd

import sys
sys.path.append('/home/martin/chesscrew/backend')

from app import create_app
from db.models import db, Tournament, TournamentPlayer, Game
from tournament_importer import import_tournament_from_excel

class TestPtsTbColumnDetection(unittest.TestCase):
    """Test Pts./TB column detection bugfix"""

    @classmethod
    def setUpClass(cls):
        """Set up Flask app context for all tests"""
        cls.app = create_app()
        cls.app_context = cls.app.app_context()
        cls.app_context.push()

    @classmethod
    def tearDownClass(cls):
        """Clean up Flask app context"""
        cls.app_context.pop()

    def setUp(self):
        """Clear database before each test"""
        Game.query.delete()
        TournamentPlayer.query.delete()
        Tournament.query.delete()
        db.session.commit()

    def create_mixed_format_excel(self):
        """Create test Excel with both Pts. and TB columns"""
        data = [
            ['From the Tournament-Database of Chess-Results https://chess-results.com', None, None, None, None, None, None, None, None, None, None, None, None, None, None, None],
            ['Test Mixed Format Tournament', None, None, None, None, None, None, None, None, None, None, None, None, None, None, None],
            ['Last update 06.09.2025 12:00:00', None, None, None, None, None, None, None, None, None, None, None, None, None, None, None],
            ['Final Ranking crosstable after 3 Rounds', None, None, None, None, None, None, None, None, None, None, None, None, None, None, None],
            ['Rk.', None, 'Name', 'FED', '1.Rd', '2.Rd', '3.Rd', 'Pts.', 'TB1', 'TB2', 'TB3', 'Rp'],
            [1, None, 'Test Player A', 'AUT', '2w1', '3b1', '4w½', 2.5, 15, 18.5, 12.5, 1650],
            [2, None, 'Regression Test Player', 'AUT', '1b0', '3w1', '4b1', 2.0, 12, 15.0, 8.0, 1580],
            [3, None, 'Test Player C', 'AUT', '1w0', '2b0', '4w1', 1.0, 8, 10.5, 4.5, 1520],
        ]
        
        df = pd.DataFrame(data)
        temp_file = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
        df.to_excel(temp_file.name, index=False, header=False)
        return temp_file.name

    def create_legacy_format_excel(self):
        """Create test Excel with only TB columns (TB1 = points)"""
        data = [
            ['From the Tournament-Database of Chess-Results https://chess-results.com', None, None, None, None, None, None, None, None, None, None, None],
            ['Test Legacy Format Tournament', None, None, None, None, None, None, None, None, None, None, None],
            ['Last update 06.09.2025 12:00:00', None, None, None, None, None, None, None, None, None, None, None],
            ['Rk.', None, 'Name', 'Rtg', 'FED', '1', '2', '3', 'TB1', 'TB2', 'TB3'],
            [1, None, 'Legacy Player A', 1500, 'AUT', '*', 1, 1, 2, 15, 0],
            [2, None, 'Legacy Player B', 1450, 'AUT', 0, '*', 1, 1, 12, 1],
            [3, None, 'Legacy Player C', 1400, 'AUT', 0, 0, '*', 0, 8, 0],
        ]
        
        df = pd.DataFrame(data)
        temp_file = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
        df.to_excel(temp_file.name, index=False, header=False)
        return temp_file.name

    def test_mixed_format_pts_tb_columns(self):
        """Test tournament with both Pts. and TB columns uses Pts. for points"""
        excel_file = self.create_mixed_format_excel()
        
        try:
            result = import_tournament_from_excel(
                excel_file,
                "Test Mixed Format",
                date=datetime(2025, 9, 6),
                chess_results_id="test_mixed_regression"
            )
            
            self.assertTrue(result and result.get('success', False), 
                           "Mixed format tournament import should succeed")
            
            tournament = Tournament.query.filter_by(chess_results_id='test_mixed_regression').first()
            self.assertIsNotNone(tournament, "Tournament should be found in database")
            
            # Find the regression test player
            test_player = None
            players = TournamentPlayer.query.filter_by(tournament_id=tournament.id).all()
            for player in players:
                if 'Regression Test Player' in player.name:
                    test_player = player
                    break
            
            self.assertIsNotNone(test_player, "Regression test player should be found")
            
            # Verify bugfix: points should come from Pts. column (2.0), not TB1 column (12.0)
            self.assertEqual(test_player.points, 2.0, 
                           "Points should be from Pts. column (2.0), not TB1 column (12.0)")
            
            # Verify tiebreaks are correctly assigned
            self.assertEqual(test_player.tiebreak1, 12.0,
                           "First tiebreak should be from TB1 column (12.0)")
            self.assertEqual(test_player.tiebreak2, 15.0,
                           "Second tiebreak should be from TB2 column (15.0)")
            
        finally:
            os.unlink(excel_file)

    def test_legacy_format_tb_only_columns(self):
        """Test tournament with only TB columns uses TB1 for points (legacy behavior)"""
        excel_file = self.create_legacy_format_excel()
        
        try:
            result = import_tournament_from_excel(
                excel_file,
                "Test Legacy Format",
                date=datetime(2025, 9, 6),
                chess_results_id="test_legacy_regression"
            )
            
            self.assertTrue(result and result.get('success', False),
                           "Legacy format tournament import should succeed")
            
            tournament = Tournament.query.filter_by(chess_results_id='test_legacy_regression').first()
            self.assertIsNotNone(tournament, "Tournament should be found in database")
            
            # Find first place player
            first_player = TournamentPlayer.query.filter_by(
                tournament_id=tournament.id, ranking=1
            ).first()
            
            self.assertIsNotNone(first_player, "First place player should be found")
            
            # Verify legacy behavior: TB1 should be used as points
            self.assertEqual(first_player.points, 2.0,
                           "Points should be from TB1 column (2.0) in legacy format")
            
            # Verify tiebreaks are correctly assigned from TB2/TB3
            self.assertEqual(first_player.tiebreak1, 15.0,
                           "First tiebreak should be from TB2 column (15.0)")
            self.assertEqual(first_player.tiebreak2, 0.0,
                           "Second tiebreak should be from TB3 column (0.0)")
            
        finally:
            os.unlink(excel_file)

    def test_regression_christina_domig_scenario(self):
        """Test specific scenario that triggered the original bug"""
        # Create Excel data that mimics the Christina Domig scenario
        data = [
            ['From the Tournament-Database of Chess-Results https://chess-results.com', None, None, None, None, None, None, None, None, None, None, None, None, None, None, None],
            ['Austrian Championship U14 Regression Test', None, None, None, None, None, None, None, None, None, None, None, None, None, None, None],
            ['Last update 29.06.2025 09:32:21', None, None, None, None, None, None, None, None, None, None, None, None, None, None, None],
            ['Final Ranking crosstable after 7 Rounds', None, None, None, None, None, None, None, None, None, None, None, None, None, None, None],
            ['Rk.', None, 'Name', 'FED', '1.Rd', '2.Rd', '3.Rd', '4.Rd', '5.Rd', '6.Rd', '7.Rd', 'Pts.', 'TB1', 'TB2', 'TB3', 'Rp'],
            [7, None, 'Christina Domig Test', 'AUT', '3w0', '-1', '4b0', '13b1', '14w½', '12b1', '6w½', 4, 23, 25.5, 11, 1530],
        ]
        
        df = pd.DataFrame(data)
        excel_file = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
        df.to_excel(excel_file.name, index=False, header=False)
        
        try:
            result = import_tournament_from_excel(
                excel_file.name,
                "Christina Domig Regression Test",
                date=datetime(2025, 6, 29),
                chess_results_id="christina_regression"
            )
            
            self.assertTrue(result and result.get('success', False),
                           "Christina Domig regression test should succeed")
            
            tournament = Tournament.query.filter_by(chess_results_id='christina_regression').first()
            self.assertIsNotNone(tournament, "Tournament should be found")
            
            christina = TournamentPlayer.query.filter_by(
                tournament_id=tournament.id
            ).first()
            
            self.assertIsNotNone(christina, "Christina should be found")
            
            # This is the core of the bugfix test
            self.assertEqual(christina.points, 4.0,
                           "Christina should have 4 points (from Pts. column), not 23 (from TB1)")
            self.assertEqual(christina.tiebreak1, 23.0,
                           "Christina's first tiebreak should be 23 (from TB1 column)")
            self.assertEqual(christina.tiebreak2, 25.5,
                           "Christina's second tiebreak should be 25.5 (from TB2 column)")
            
        finally:
            os.unlink(excel_file.name)

if __name__ == '__main__':
    # Set environment variable for testing
    os.environ['FLASK_SECRET_KEY'] = 'test-secret-key'
    unittest.main(verbosity=2)
