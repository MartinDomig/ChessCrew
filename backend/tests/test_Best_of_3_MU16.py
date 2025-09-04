#!/usr/bin/env python3
"""
Test for Best of 3 match format tournament: Vbg. Landesmeisterschaft 2025 - MU16

This is an unusual "tournament" that's actually a head-to-head Best of 3 match between 2 players.
Tournament URL: https://s2.chess-results.com/tnr1112992.aspx

Expected characteristics:
- Only 2 players
- Best of 3 format (not Swiss system)
- Result shown as: Bülow Mattea - Ganeva Marie -- 2 : 0
- May not have traditional round structure
"""

import sys
import os
import logging
from datetime import datetime

# Add backend to path
sys.path.append('/home/martin/chesscrew/backend')

from app import create_app
from db.models import db, Tournament, TournamentPlayer, Game
from chess_results_crawler import ChessResultsCrawler

def test_best_of_3_import():
    """Test importing a Best of 3 match format tournament"""
    
    # Tournament URL and expected ID
    tournament_url = "https://s2.chess-results.com/tnr1112992.aspx"
    expected_tournament_id = 1112992
    
    print(f"🧪 Testing Best of 3 match import from: {tournament_url}")
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
        
        # Initialize the crawler
        crawler = ChessResultsCrawler()
        
        # Step 1: Login
        print("🔐 Step 1: Login...")
        login_success = crawler.login()
        if not login_success:
            print("❌ Login failed")
            return False
        print("✅ Login successful")
        print()
        
        # Step 2: Get tournament details
        print("� Step 2: Getting tournament details...")
        tournament_details = crawler.get_tournament_details(tournament_url, expected_tournament_id)
        if not tournament_details:
            print("❌ Failed to get tournament details")
            return False
        print("✅ Got tournament details")
        print(f"   Final table URL: {tournament_details.get('final_table_url', 'N/A')}")
        print()
        
        # Step 3: Download Excel file
        print("📥 Step 3: Downloading Excel file...")
        excel_file = crawler.download_excel_export(tournament_details)
        if not excel_file:
            print("❌ Failed to download Excel file")
            return False
        print(f"✅ Downloaded Excel file: {excel_file}")
        print()
        
        # Step 4: Import tournament
        print("📥 Step 4: Importing tournament data...")
        success = crawler.import_tournament_from_excel_file(excel_file, "Vbg. Landesmeisterschaft 2025 - MU16", expected_tournament_id)
        
        if not success:
            print("❌ Tournament import failed!")
            return False
            
        print("✅ Tournament import completed!")
        print()
        
        # Query the database for tournament data
        tournament = Tournament.query.filter_by(chess_results_id=expected_tournament_id).first()
        
        if not tournament:
            print(f"❌ Tournament with ID {expected_tournament_id} not found in database!")
            return False
            
        print(f"🏆 Tournament found: {tournament.name}")
        print(f"📅 Date: {tournament.date}")
        print(f"🌍 Location: {tournament.location}")
        print(f"🔢 Chess-results ID: {tournament.chess_results_id}")
        print()
        
        # Get all players in this tournament
        tournament_players = TournamentPlayer.query.filter_by(tournament_id=tournament.id).all()
        player_count = len(tournament_players)
        
        print(f"👥 Players in tournament: {player_count}")
        
        # List all players
        for tp in tournament_players:
            print(f"   - {tp.name} (Rating: {tp.rating}, Title: {tp.title})")
        print()
        
        # Analyze game/result structure
        # Check games table for actual game data
        all_games = Game.query.filter_by(tournament_id=tournament.id).all()
        games_count = len(all_games)
        
        rounds = set()
        for game in all_games:
            rounds.add(game.round_number)
        
        rounds_count = len(rounds)
        
        print(f"🎯 Rounds detected: {rounds_count}")
        print(f"🎮 Games played: {games_count}")
        print()
        
        # Validation for Best of 3 format
        print("🔍 Validating Best of 3 format...")
        
        # Check 1: Should have exactly 2 players
        if player_count != 2:
            print(f"❌ Expected 2 players, found {player_count}")
            return False
        print("✅ Player count: 2 players ✓")
        
        # Check 2: Should be a head-to-head match
        if len(tournament_players) == 2:
            player1, player2 = tournament_players
            print(f"✅ Head-to-head: {player1.name} vs {player2.name} ✓")
        
        # Check 3: Tournament ID should match
        if int(tournament.chess_results_id) != int(expected_tournament_id):
            print(f"❌ Expected tournament ID {expected_tournament_id}, found {tournament.chess_results_id}")
            return False
        print(f"✅ Tournament ID: {expected_tournament_id} ✓")
        
        # Check 4: Should have some game structure (even if unusual)
        if rounds_count == 0:
            print("⚠️  Warning: No rounds detected - this might be a final result only")
        else:
            print(f"✅ Rounds structure: {rounds_count} rounds ✓")
        
        # Summary
        print()
        print("📊 Best of 3 Tournament Summary:")
        print(f"   Tournament: {tournament.name}")
        print(f"   Players: {player_count}")
        print(f"   Rounds: {rounds_count}")
        print(f"   Games: {games_count}")
        print(f"   Format: Best of 3 match")
        print()
        
        print("🎉 Best of 3 match test PASSED! ✅")
        print("🤝 System successfully handles head-to-head match formats!")
        
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
        success = test_best_of_3_import()
        sys.exit(0 if success else 1)
