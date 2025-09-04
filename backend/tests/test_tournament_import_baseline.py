#!/usr/bin/env python3
"""
BASELINE Tournament Import Test Script
=====================================
This script tests the WORKING tournament import functionality.
Keep this as a reference/regression test while working on importer improvements.

Features tested:
- Chess-results.com login and authentication
- Tournament details extraction with form submission for older tournaments  
- Excel export download from final table page (with "Show tournament details" resubmission)
- Complex round result parsing (format: "2w1" = opponent 2, white color, win)
- Complete game import with round numbers, colors, and results
- Tiebreak scores (TB1, TB2) import and storage
- Database relationships and data integrity

Last verified working: September 5, 2025
Test tournament: https://s3.chess-results.com/tnr1152295.aspx (Vbg. Landesmeisterschaft 2025 - U8)
"""

import os
import sys
import logging
from datetime import datetime

# Add backend to path
sys.path.append('/home/martin/chesscrew/backend')

from app import create_app
from db.models import db, Tournament, TournamentPlayer, Game
from chess_results_crawler import ChessResultsCrawler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s'
)
logger = logging.getLogger(__name__)

def clear_tournament_data():
    """Clear all tournament-related data from database"""
    logger.info("=== Clearing Tournament Data ===")
    
    # Delete in correct order to avoid foreign key constraints
    games_deleted = Game.query.delete()
    logger.info(f"Deleted {games_deleted} games")
    
    tournament_players_deleted = TournamentPlayer.query.delete()
    logger.info(f"Deleted {tournament_players_deleted} tournament players")
    
    tournaments_deleted = Tournament.query.delete()
    logger.info(f"Deleted {tournaments_deleted} tournaments")
    
    db.session.commit()
    logger.info("✅ Database cleared successfully")

def validate_tournament_data(tournament_id_str):
    """Validate imported tournament data with expected values"""
    logger.info("=== Validating Tournament Data ===")
    
    # Check tournament exists
    tournament = Tournament.query.filter_by(chess_results_id=tournament_id_str).first()
    if not tournament:
        logger.error(f"❌ Tournament with chess_results_id {tournament_id_str} not found")
        return False
    
    logger.info(f"✅ Tournament found: {tournament.name}")
    logger.info(f"   ID: {tournament.id}")
    logger.info(f"   Chess Results ID: {tournament.chess_results_id}")
    logger.info(f"   Date: {tournament.date}")
    logger.info(f"   Location: {tournament.location}")
    
    # Validate tournament metadata
    validation_errors = []
    if tournament.name != "Vbg. Landesmeisterschaft 2025 - U8":
        validation_errors.append(f"Tournament name mismatch: expected 'Vbg. Landesmeisterschaft 2025 - U8', got '{tournament.name}'")
    
    # Check tournament players
    tournament_players = TournamentPlayer.query.filter_by(tournament_id=tournament.id).order_by(TournamentPlayer.ranking).all()
    logger.info(f"✅ Found {len(tournament_players)} tournament players")
    
    # Expected player data from the Ebensee tournament (ordered by final ranking)
    # Updated with actual imported values from the U8 championship
    expected_players = [
        {"rank": 1, "name": "Burgstaller Jonathan", "points": 5.0, "tb1": 10.5, "tb2": 11.5},
        {"rank": 2, "name": "Umundum Nathanael", "points": 3.0, "tb1": 12.5, "tb2": 13.0},
        {"rank": 3, "name": "Wabnig Felix", "points": 3.0, "tb1": 11.0, "tb2": 11.5},
        {"rank": 4, "name": "Blum Vincent", "points": 3.0, "tb1": 9.5, "tb2": 10.0},
        {"rank": 5, "name": "Abdouni Adam", "points": 2.5, "tb1": 13.0, "tb2": 13.5},
        {"rank": 6, "name": "Zhou Zihan", "points": 2.0, "tb1": 13.5, "tb2": 14.5},
        {"rank": 7, "name": "Höfel Tabea", "points": 1.0, "tb1": 13.0, "tb2": 13.5},
        {"rank": 8, "name": "Ortner Isabella", "points": 0.5, "tb1": 11.5, "tb2": 12.5},
    ]
    
    if len(tournament_players) != len(expected_players):
        validation_errors.append(f"Player count mismatch: expected {len(expected_players)}, got {len(tournament_players)}")
    
    # Validate each player's data
    for i, tp in enumerate(tournament_players):
        if i >= len(expected_players):
            break
            
        expected = expected_players[i]
        
        logger.info(f"   Player {tp.ranking}: {tp.name}")
        logger.info(f"     Tournament Points: {tp.points}")
        logger.info(f"     Tiebreak 1: {tp.tiebreak1}")
        logger.info(f"     Tiebreak 2: {tp.tiebreak2}")
        
        # Validate player data against expected values
        if tp.ranking != expected["rank"]:
            validation_errors.append(f"Ranking mismatch for {tp.name}: expected {expected['rank']}, got {tp.ranking}")
        
        # Normalize names for comparison (handle different ordering)
        expected_name_parts = set(expected["name"].lower().split())
        actual_name_parts = set(tp.name.lower().split())
        if expected_name_parts != actual_name_parts:
            validation_errors.append(f"Name mismatch for rank {tp.ranking}: expected '{expected['name']}', got '{tp.name}'")
        
        if tp.points != expected["points"]:
            validation_errors.append(f"Points mismatch for {tp.name}: expected {expected['points']}, got {tp.points}")
        
        if tp.tiebreak1 != expected["tb1"]:
            validation_errors.append(f"Tiebreak1 mismatch for {tp.name}: expected {expected['tb1']}, got {tp.tiebreak1}")
        
        if tp.tiebreak2 != expected["tb2"]:
            validation_errors.append(f"Tiebreak2 mismatch for {tp.name}: expected {expected['tb2']}, got {tp.tiebreak2}")
    
    # Check games
    games = Game.query.filter_by(tournament_id=tournament.id).all()
    logger.info(f"✅ Found {len(games)} games")
    
    # Expected game results from the crosstable (sample verification)
    # Format: [round, player_name, opponent_name, expected_result, player_color]
    # Updated with actual imported values from the U8 championship
    expected_games = [
        # Round 1 results (sample)
        (1, "Burgstaller Jonathan", "Höfel Tabea", "1", "black"),        # 7b1
        (1, "Umundum Nathanael", "Blum Vincent", "1", "white"),          # 4w1
        (1, "Wabnig Felix", "Zhou Zihan", "0", "white"),                 # 6w0
        (1, "Abdouni Adam", "Ortner Isabella", "1", "white"),            # 8w1
        # Round 2 results (sample)
        (2, "Burgstaller Jonathan", "Umundum Nathanael", "1", "white"),  # 2w1
        (2, "Wabnig Felix", "Ortner Isabella", "1", "black"),            # 8b1
        (2, "Blum Vincent", "Höfel Tabea", "1", "white"),                # 7w1
        (2, "Abdouni Adam", "Zhou Zihan", "1", "black"),                 # 6b1
    ]
    
    # Validate sample games
    games_by_lookup = {}
    for game in games:
        player_tp = TournamentPlayer.query.get(game.player_id)
        opponent_tp = TournamentPlayer.query.get(game.opponent_id)
        if player_tp and opponent_tp:
            key = (game.round_number, player_tp.name)
            games_by_lookup[key] = {
                'opponent': opponent_tp.name,
                'result': str(game.result),
                'color': game.player_color
            }
    
    # Verify expected games
    for expected_game in expected_games:
        round_num, player_name, opponent_name, expected_result, expected_color = expected_game
        key = (round_num, player_name)
        
        if key in games_by_lookup:
            actual_game = games_by_lookup[key]
            
            # Check opponent
            if actual_game['opponent'] != opponent_name:
                validation_errors.append(f"Round {round_num} opponent mismatch for {player_name}: expected {opponent_name}, got {actual_game['opponent']}")
            
            # Check result
            if actual_game['result'] != expected_result:
                validation_errors.append(f"Round {round_num} result mismatch for {player_name} vs {opponent_name}: expected {expected_result}, got {actual_game['result']}")
            
            # Check color
            if actual_game['color'] != expected_color:
                validation_errors.append(f"Round {round_num} color mismatch for {player_name} vs {opponent_name}: expected {expected_color}, got {actual_game['color']}")
        else:
            validation_errors.append(f"Expected game not found: Round {round_num}, {player_name} vs {opponent_name}")
    
    # Validate total games count and structure
    expected_total_games = 40  # 8 players * 5 rounds = 40 games
    if len(games) != expected_total_games:
        validation_errors.append(f"Total games mismatch: expected {expected_total_games}, got {len(games)}")
    
    # Validate each player has exactly 5 games
    for tp in tournament_players:
        player_games = Game.query.filter(
            db.or_(
                Game.player_id == tp.id,
                Game.opponent_id == tp.id
            ),
            Game.tournament_id == tournament.id
        ).count()
        
        if player_games != 10:  # Each player appears in 5 games as player + 5 games as opponent = 10 total
            validation_errors.append(f"Game count mismatch for {tp.name}: expected 10, got {player_games}")
    
    # Report validation results
    if validation_errors:
        logger.error("❌ Data validation errors:")
        for error in validation_errors:
            logger.error(f"   {error}")
        return False
    
    # Summary statistics
    logger.info("=== Summary Statistics ===")
    logger.info(f"Tournament: {tournament.name}")
    logger.info(f"Players: {len(tournament_players)}")
    logger.info(f"Games: {len(games)}")
    logger.info(f"Rounds: {max([g.round_number for g in games]) if games else 0}")
    
    logger.info("✅ ALL DATA VALIDATION PASSED - Tournament data is accurate!")
    return True

def baseline_tournament_test():
    """Run baseline tournament import test"""
    
    print("Chess Results Crawler - BASELINE Tournament Test")
    print("This test validates the WORKING tournament import functionality")
    print("Tournament: https://s3.chess-results.com/tnr1152295.aspx")
    print("=" * 70)
    
    # Create Flask app context
    app = create_app()
    with app.app_context():
        
        logger.info("=== Starting BASELINE Tournament Test ===")
        
        # Step 1: Clear database
        clear_tournament_data()
        
        # Step 2: Initialize crawler and login
        logger.info("\n--- Step 1: Login ---")
        crawler = ChessResultsCrawler()
        if not crawler.login():
            logger.error("❌ Login failed")
            return False
        logger.info("✅ Login successful")
        
        # Step 3: Import tournament
        logger.info("\n--- Step 2: Import Tournament ---")
        tournament_url = "https://s3.chess-results.com/tnr1152295.aspx"
        tournament_id = "1152295"
        
        # Get tournament details
        details = crawler.get_tournament_details(tournament_url, tournament_id)
        if not details:
            logger.error("❌ Could not get tournament details")
            return False
        
        logger.info("✅ Got tournament details")
        if 'excel_url' in details:
            logger.info(f"   Excel export URL: {details['excel_url']}")
        else:
            logger.info(f"   Final table URL: {details['final_table_url']}")
        
        # Download Excel file
        excel_file = crawler.download_excel_export(details)
        if not excel_file:
            logger.error("❌ Could not download Excel file")
            return False
        
        logger.info(f"✅ Downloaded Excel file: {excel_file}")
        
        # Import tournament
        result = crawler.import_tournament_from_excel_file(excel_file, f"Vbg. Landesmeisterschaft 2025 - U8", tournament_id)
        if not result.get('success'):
            logger.error(f"❌ Tournament import failed: {result.get('error')}")
            return False
        
        logger.info("✅ Tournament imported successfully")
        logger.info(f"   Tournament: {result.get('tournament_name')}")
        logger.info(f"   Players: {result.get('imported_players')}")
        logger.info(f"   Games: {result.get('imported_games')}")
        
        # Step 4: Validate imported data
        logger.info("\n--- Step 3: Validate Data ---")
        validation_success = validate_tournament_data(tournament_id)
        
        if validation_success:
            logger.info("\n🎉 BASELINE tournament test PASSED!")
            logger.info("✅ All functionality working as expected")
            return True
        else:
            logger.error("\n❌ BASELINE tournament test FAILED!")
            logger.error("⚠️ Working functionality has been broken!")
            return False

if __name__ == "__main__":
    try:
        success = baseline_tournament_test()
        exit_code = 0 if success else 1
        sys.exit(exit_code)
    except Exception as e:
        logger.error(f"Baseline test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
