#!/usr/bin/env python3
"""
Quick verification test for the Pts./TB column detection bugfix

This is a minimal test that can be run to quickly verify the bugfix is working.
It specifically tests the Christina Domig scenario where 23 points (TB1) 
was being imported instead of 4 points (Pts.).
"""

import sys
import os
import tempfile
import pandas as pd
from datetime import datetime

# Add backend to path
sys.path.append('/home/martin/chesscrew/backend')

def test_bugfix_quick():
    """Quick test to verify the bugfix is working"""
    try:
        from app import create_app
        from db.models import db, Tournament, TournamentPlayer, Game
        from tournament_importer import import_tournament_from_excel
        
        app = create_app()
        with app.app_context():
            # Clear database
            Game.query.delete()
            TournamentPlayer.query.delete()
            Tournament.query.delete()
            db.session.commit()
            
            # Create test data with both Pts. and TB columns
            data = [
                ['Test Tournament', None, None, None, None, None, None, None, None],
                ['Rk.', None, 'Name', 'FED', '1.Rd', 'Pts.', 'TB1', 'TB2', 'TB3'],
                [1, None, 'Test Player', 'AUT', '2w1', 4.0, 23.0, 25.5, 11.0],
            ]
            
            df = pd.DataFrame(data)
            temp_file = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
            df.to_excel(temp_file.name, index=False, header=False)
            
            # Import tournament
            result = import_tournament_from_excel(
                temp_file.name,
                "Bugfix Verification Test",
                date=datetime(2025, 9, 6),
                chess_results_id="bugfix_test"
            )
            
            # Check result
            if result and result.get('success'):
                tournament = Tournament.query.filter_by(chess_results_id='bugfix_test').first()
                if tournament:
                    player = TournamentPlayer.query.filter_by(tournament_id=tournament.id).first()
                    if player:
                        if player.points == 4.0 and player.tiebreak1 == 23.0:
                            print("✅ BUGFIX VERIFICATION PASSED")
                            print(f"   Points: {player.points} (correct - from Pts. column)")
                            print(f"   Tiebreak 1: {player.tiebreak1} (correct - from TB1 column)")
                            return True
                        else:
                            print("❌ BUGFIX VERIFICATION FAILED")
                            print(f"   Points: {player.points} (expected 4.0)")
                            print(f"   Tiebreak 1: {player.tiebreak1} (expected 23.0)")
                            return False
            
            print("❌ BUGFIX VERIFICATION FAILED - Import unsuccessful")
            return False
            
    except Exception as e:
        print(f"❌ BUGFIX VERIFICATION FAILED - Error: {e}")
        return False
    finally:
        try:
            os.unlink(temp_file.name)
        except:
            pass

if __name__ == "__main__":
    os.environ['FLASK_SECRET_KEY'] = 'test-secret-key'
    success = test_bugfix_quick()
    sys.exit(0 if success else 1)
