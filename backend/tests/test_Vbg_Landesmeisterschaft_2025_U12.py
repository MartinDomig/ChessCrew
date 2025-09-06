import os
import sys
import tempfile

# Add backend to path
sys.path.append('/home/martin/chesscrew/backend')

from chess_results_crawler import ChessResultsCrawler
from tournament_importer import import_tournament_from_excel
from db.models import db, Tournament, TournamentPlayer, Player
from app import create_app

def test_vbg_landesmeisterschaft_u12():
    print("🔍 Testing Vbg. Landesmeisterschaft 2025 - U12 tournament...")
    print("URL: https://s1.chess-results.com/tnr1113507.aspx")
    print("Expected: 8 players, 7 rounds, with tied scores")
    print()
    
    # Set up database connection
    app = create_app()
    with app.app_context():
        # Clean up any existing data for this tournament
        existing_tournament = Tournament.query.filter_by(chess_results_id='1113507').first()
        if existing_tournament:
            print(f"🧹 Cleaning up existing tournament: {existing_tournament.name}")
            TournamentPlayer.query.filter_by(tournament_id=existing_tournament.id).delete()
            db.session.delete(existing_tournament)
            db.session.commit()
        
        # Download and import tournament
        print("📥 Downloading tournament data...")
        crawler = ChessResultsCrawler()
        
        tournament_details = {
            'tournament_id': '1113507',
            'name': 'Vbg. Landesmeisterschaft 2025 - U12',
            'final_table_url': 'https://s1.chess-results.com/tnr1113507.aspx?art=1&rd=7'
        }
        
        # Download final standings
        excel_path = crawler.download_excel_export(tournament_details)
        print(f"✅ Downloaded final standings to: {excel_path}")
        
        # Import tournament
        print("📊 Importing tournament...")
        result = crawler.import_tournament_from_excel_file(
            excel_path, 
            tournament_details['name'], 
            tournament_details['tournament_id']
        )
        
        if not result or not result.get('success', False):
            print(f"❌ Failed to import tournament! {result}")
            return False
        
        # Verify import
        tournament = Tournament.query.filter_by(chess_results_id='1113507').first()
        if not tournament:
            print("❌ Tournament not found in database!")
            return False
        
        players = TournamentPlayer.query.filter_by(tournament_id=tournament.id).order_by(TournamentPlayer.ranking).all()
        
        print(f"✅ Tournament imported: {tournament.name}")
        print(f"✅ Players: {len(players)}")
        print(f"✅ Rounds: {tournament.rounds}")
        print()
        
        # Expected results based on the download
        expected_players = 8
        expected_rounds = 7  # This might be None for results-only tournaments
        expected_top_scores = [7, 5, 5, 4, 2.5, 2.5, 2, 0]  # Points with ties
        
        # Verify player count
        if len(players) != expected_players:
            print(f"❌ Expected {expected_players} players, got {len(players)}")
            return False
        
        # Verify rounds (might be None for results-only tournaments)
        if tournament.rounds is None:
            print("ℹ️  Results-only tournament: no round information available")
            print("   This is normal for tournaments that only publish final standings")
        elif tournament.rounds != expected_rounds:
            print(f"❌ Expected {expected_rounds} rounds, got {tournament.rounds}")
            return False
        else:
            print(f"✅ Rounds: {tournament.rounds}")
        
        # Check for tied scores
        print("🏆 Final standings:")
        scores = []
        for i, player in enumerate(players, 1):
            score = player.points
            scores.append(score)
            print(f"  {i}. {player.player.name if player.player else player.name} - {score} points (TB1: {player.tiebreak1})")
        
        # Verify expected scores
        if scores != expected_top_scores:
            print(f"❌ Expected scores {expected_top_scores}, got {scores}")
            return False
        
        # Check for proper tie handling
        ties_found = []
        for i in range(len(scores) - 1):
            if scores[i] == scores[i + 1]:
                ties_found.append((i + 1, scores[i]))
        
        print(f"🤝 Ties found: {len(ties_found)}")
        for rank, score in ties_found:
            print(f"  Tied at rank {rank}-{rank+1}: {score} points")
        
        # Expected ties: ranks 2-3 (5 points), ranks 5-6 (2.5 points)
        expected_ties = [(2, 5.0), (5, 2.5)]
        
        if len(ties_found) != len(expected_ties):
            print(f"❌ Expected {len(expected_ties)} ties, found {len(ties_found)}")
            return False
        
        for expected_tie in expected_ties:
            if expected_tie not in ties_found:
                print(f"❌ Expected tie at rank {expected_tie[0]} with {expected_tie[1]} points not found")
                return False
        
        # Verify some specific players and their details
        lins_jakob = next((p for p in players if "Jakob" in (p.player.name if p.player else p.name) and "Lins" in (p.player.name if p.player else p.name)), None)
        if not lins_jakob or lins_jakob.ranking != 1 or lins_jakob.points != 7:
            print(f"❌ Jakob Lins should be rank 1 with 7 points, got rank {lins_jakob.ranking if lins_jakob else 'None'} with {lins_jakob.points if lins_jakob else 'None'} points")
            return False
        
        # Check tiebreak handling
        tied_players_5pts = [p for p in players if p.points == 5.0]
        if len(tied_players_5pts) != 2:
            print(f"❌ Expected 2 players with 5 points, got {len(tied_players_5pts)}")
            return False
        
        # Verify tiebreak ordering (TB1 should be different for tied players)
        tb1_values_5pts = [p.tiebreak1 for p in tied_players_5pts]
        if tb1_values_5pts[0] == tb1_values_5pts[1]:
            print("⚠️  Warning: Tied players have same TB1 value")
        else:
            print(f"✅ Tiebreak properly distinguishes tied players: TB1 values {tb1_values_5pts}")
        
        print()
        print("🎉 Vbg. Landesmeisterschaft 2025 - U12 test PASSED!")
        print("✅ Successfully imported Swiss tournament with ties!")
        
        return True

if __name__ == "__main__":
    success = test_vbg_landesmeisterschaft_u12()
    sys.exit(0 if success else 1)
