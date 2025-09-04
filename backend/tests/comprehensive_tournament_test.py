#!/usr/bin/env python3
"""
Comprehensive tournament import test script
- Clears database tables (tournaments, games, tournament_players)
- Imports complete tournament data
- Validates all imported data
"""

import os
import sys
import logging
from datetime import datetime

# Add backend to path
sys.path.append('/home/martin/chesscrew/backend')

from app import create_app
from db.models import db, Tournament, TournamentPlayer, Game, Player
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
    """Validate imported tournament data"""
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
    
    # Check tournament players
    tournament_players = TournamentPlayer.query.filter_by(tournament_id=tournament.id).all()
    logger.info(f"✅ Found {len(tournament_players)} tournament players")
    
    # Validate each player
    player_validation_errors = []
    for tp in tournament_players:
        player = Player.query.get(tp.player_id)
        if not player:
            player_validation_errors.append(f"Player ID {tp.player_id} not found")
            continue
        
        logger.info(f"   Player: {player.name} (ID: {player.id})")
        logger.info(f"     Country: {player.country}")
        logger.info(f"     Tournament Points: {tp.points}")
        logger.info(f"     Tournament Ranking: {tp.ranking}")
        logger.info(f"     Tiebreak 1: {tp.tiebreak1}")
        logger.info(f"     Tiebreak 2: {tp.tiebreak2}")
        logger.info(f"     Chess Results ID: {tp.chess_results_id}")
        
        # Validate required fields
        if not player.name:
            player_validation_errors.append(f"Player {player.id} missing name")
    
    if player_validation_errors:
        logger.error("❌ Player validation errors:")
        for error in player_validation_errors:
            logger.error(f"   {error}")
        return False
    
    # Check games
    games = Game.query.filter_by(tournament_id=tournament.id).all()
    logger.info(f"✅ Found {len(games)} games")
    
    # Validate games
    game_validation_errors = []
    for game in games:
        player_tp = TournamentPlayer.query.get(game.player_id)
        opponent_tp = TournamentPlayer.query.get(game.opponent_id)
        
        if not player_tp:
            game_validation_errors.append(f"Game {game.id} - Player tournament entry {game.player_id} not found")
        if not opponent_tp:
            game_validation_errors.append(f"Game {game.id} - Opponent tournament entry {game.opponent_id} not found")
        
        if player_tp and opponent_tp:
            player = Player.query.get(player_tp.player_id) if player_tp.player_id else None
            opponent = Player.query.get(opponent_tp.player_id) if opponent_tp.player_id else None
            
            player_name = player.name if player else player_tp.name
            opponent_name = opponent.name if opponent else opponent_tp.name
            
            logger.info(f"   Game {game.round_number}: {player_name} vs {opponent_name} = {game.result}")
            
            # Validate game result
            if game.result not in ['1', '0', '1/2', '1-0', '0-1', '1/2-1/2', '*', '½', 0, 1, 0.5]:
                game_validation_errors.append(f"Game {game.id} - Invalid result: {game.result}")
    
    if game_validation_errors:
        logger.error("❌ Game validation errors:")
        for error in game_validation_errors:
            logger.error(f"   {error}")
        return False
    
    # Cross-validation: Check if all tournament players have games
    logger.info("=== Cross-Validation ===")
    for tp in tournament_players:
        player_games = Game.query.filter(
            db.or_(
                Game.player_id == tp.id,
                Game.opponent_id == tp.id
            ),
            Game.tournament_id == tournament.id
        ).count()
        
        player = Player.query.get(tp.player_id) if tp.player_id else None
        player_name = player.name if player else tp.name
        logger.info(f"   {player_name}: {player_games} games")
    
    # Summary statistics
    logger.info("=== Summary Statistics ===")
    logger.info(f"Tournament: {tournament.name}")
    logger.info(f"Players: {len(tournament_players)}")
    logger.info(f"Games: {len(games)}")
    logger.info(f"Rounds: {max([g.round_number for g in games]) if games else 0}")
    
    # Calculate expected number of games
    num_players = len(tournament_players)
    if num_players > 0:
        num_rounds = max([g.round_number for g in games]) if games else 0
        expected_games = (num_players * num_rounds) // 2  # Each round, each player plays once
        logger.info(f"Expected games (approx): {expected_games}")
        
        if len(games) < expected_games * 0.8:  # Allow some tolerance
            logger.warning(f"⚠️ Game count seems low (expected ~{expected_games}, got {len(games)})")
    
    logger.info("✅ Data validation completed successfully")
    return True

def comprehensive_tournament_test():
    """Run comprehensive tournament import test"""
    
    print("Chess Results Crawler - Comprehensive Tournament Test")
    print("Tournament: https://s3.chess-results.com/tnr1152295.aspx")
    print("=" * 60)
    
    # Create Flask app context
    app = create_app()
    with app.app_context():
        
        logger.info("=== Starting Comprehensive Tournament Test ===")
        
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
            logger.info("\n🎉 Comprehensive tournament test PASSED!")
            return True
        else:
            logger.error("\n❌ Comprehensive tournament test FAILED!")
            return False

if __name__ == "__main__":
    try:
        success = comprehensive_tournament_test()
        exit_code = 0 if success else 1
        sys.exit(exit_code)
    except Exception as e:
        logger.error(f"Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
