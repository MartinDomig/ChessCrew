#!/usr/bin/env python3
"""
Test for U10 tournament: Vbg. Landesmeisterschaft 2025 - U10

This tournament appears to be from the same series as the MU16 but for U10 category.
Tournament URL: https://s3.chess-results.com/tnr1112981.aspx

Expected characteristics:
- 8 players (similar to our baseline tests)
- Regular Swiss system format (unlike the Best of 3)
- U10 age category
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

def test_u10_tournament_import():
    """Test importing U10 tournament"""
    
    # Tournament URL and expected ID
    tournament_url = "https://s3.chess-results.com/tnr1112981.aspx"
    expected_tournament_id = 1112981
    
    print(f"🧪 Testing U10 tournament import from: {tournament_url}")
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
        print("📋 Step 2: Getting tournament details...")
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
        
        # Step 3b: Try to download cross table for round data
        print("📋 Step 3b: Downloading cross table...")
        cross_table_file = crawler.download_cross_table_excel(tournament_details)
        if cross_table_file:
            print(f"✅ Downloaded cross table: {cross_table_file}")
        else:
            print("⚠️  Cross table not available")
        print()
        
        # Step 4: Import tournament
        print("📥 Step 4: Importing tournament data...")
        
        # Try to import with cross table data if available
        if cross_table_file:
            # For now, we'll use the regular import but pass the cross table file separately
            # We need to enhance the import function to accept cross table data
            success = crawler.import_tournament_from_excel_file(excel_file, "Vbg. Landesmeisterschaft 2025 - U10", expected_tournament_id)
            
            if success and cross_table_file:
                # After regular import, try to parse cross table for games
                print("📋 Step 4b: Parsing cross table for game data...")
                from tournament_importer import parse_cross_table_games
                
                # Get the imported tournament and players
                tournament = Tournament.query.filter_by(chess_results_id=str(expected_tournament_id)).first()
                tournament_players = TournamentPlayer.query.filter_by(tournament_id=tournament.id).all()
                
                # Parse cross table games
                cross_table_games = parse_cross_table_games(cross_table_file, tournament_players, tournament)
                print(f"✅ Imported {cross_table_games} additional games from cross table")
                
                # Commit the cross table games
                db.session.commit()
        else:
            success = crawler.import_tournament_from_excel_file(excel_file, "Vbg. Landesmeisterschaft 2025 - U10", expected_tournament_id)
        
        if not success:
            print("❌ Tournament import failed!")
            return False
            
        print("✅ Tournament import completed!")
        print()
        
        # Query the database for tournament data
        tournament = Tournament.query.filter_by(chess_results_id=str(expected_tournament_id)).first()
        
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
        for tp in sorted(tournament_players, key=lambda x: x.ranking or 999):
            print(f"   {tp.ranking}. {tp.name} (Rating: {tp.rating}, Points: {tp.points})")
        print()
        
        # Analyze game/result structure
        all_games = Game.query.filter_by(tournament_id=tournament.id).all()
        games_count = len(all_games)
        
        rounds = set()
        for game in all_games:
            rounds.add(game.round_number)
        
        rounds_count = len(rounds)
        
        print(f"🎯 Rounds detected: {rounds_count}")
        print(f"🎮 Games played: {games_count}")
        print()
        
        # Validation
        print("🔍 Validating U10 tournament...")
        
        # Check 1: Should have expected number of players
        if player_count < 5 or player_count > 12:
            print(f"⚠️  Unexpected player count: {player_count} (expected ~8)")
        else:
            print(f"✅ Player count: {player_count} players ✓")
        
        # Check 2: Tournament ID should match
        if int(tournament.chess_results_id) != int(expected_tournament_id):
            print(f"❌ Expected tournament ID {expected_tournament_id}, found {tournament.chess_results_id}")
            return False
        print(f"✅ Tournament ID: {expected_tournament_id} ✓")
        
        # Check 3: Should have reasonable number of games for player count
        expected_min_games = player_count * 2  # Conservative estimate
        if games_count >= expected_min_games:
            print(f"✅ Game count: {games_count} games (reasonable for {player_count} players) ✓")
        else:
            print(f"⚠️  Low game count: {games_count} games for {player_count} players")
        
        # Check 4: Should have rounds
        if rounds_count > 0:
            print(f"✅ Rounds structure: {rounds_count} rounds ✓")
        else:
            print("⚠️  No rounds detected")
        
        # Summary
        print()
        print("📊 U10 Tournament Summary:")
        print(f"   Tournament: {tournament.name}")
        print(f"   Players: {player_count}")
        print(f"   Rounds: {rounds_count}")
        print(f"   Games: {games_count}")
        print(f"   Category: U10")
        print()
        
        print("🎉 U10 tournament test PASSED! ✅")
        print("🔍 Successfully imported regular Swiss tournament!")
        
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
        success = test_u10_tournament_import()
        sys.exit(0 if success else 1)
