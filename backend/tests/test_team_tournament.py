import os
import sys
import tempfile

# Add backend to path
sys.path.append('/home/martin/chesscrew/backend')

from chess_results_crawler import ChessResultsCrawler
from tournament_importer import import_tournament_from_excel
from db.models import db, Tournament, TournamentPlayer, Player
from app import create_app

def test_team_tournament():
    print("🔍 Testing Team Tournament (Individual Players Only)...")
    print("URL: https://s2.chess-results.com/tnr999316.aspx")
    print("Expected: Extract individual player results, ignore team structure")
    print()
    
    # Set up database connection
    app = create_app()
    with app.app_context():
        # Clean up any existing data for this tournament
        existing_tournament = Tournament.query.filter_by(chess_results_id='999316').first()
        if existing_tournament:
            print(f"🧹 Cleaning up existing tournament: {existing_tournament.name}")
            TournamentPlayer.query.filter_by(tournament_id=existing_tournament.id).delete()
            db.session.delete(existing_tournament)
            db.session.commit()
        
        # Download and import tournament
        print("📥 Downloading tournament data...")
        crawler = ChessResultsCrawler()
        
        tournament_details = {
            'tournament_id': '999316',
            'name': 'Vorarlberger Landesmannschaftsmeisterschaft 2024-25, A-Klasse',
            'final_table_url': 'https://s2.chess-results.com/tnr999316.aspx?art=1'
        }
        
        # Download final standings (team composition)
        excel_path = crawler.download_excel_export(tournament_details)
        print(f"✅ Downloaded team tournament data to: {excel_path}")
        
        # Import tournament
        print("📊 Importing team tournament (individual players only)...")
        result = crawler.import_tournament_from_excel_file(
            excel_path, 
            tournament_details['name'], 
            tournament_details['tournament_id']
        )
        
        if not result or not result.get('success', False):
            print(f"❌ Failed to import tournament! {result}")
            return False
        
        # Verify import
        tournament = Tournament.query.filter_by(chess_results_id='999316').first()
        if not tournament:
            print("❌ Tournament not found in database!")
            return False
        
        players = TournamentPlayer.query.filter_by(tournament_id=tournament.id).all()
        
        print(f"✅ Tournament imported: {tournament.name}")
        print(f"✅ Players: {len(players)}")
        print(f"✅ Is Team Tournament: {tournament.is_team}")
        print()
        
        # Analyze individual player results
        print("👥 Individual Player Results (sample):")
        sample_players = players[:10]  # Show first 10 players
        for player in sample_players:
            player_name = player.player.name if player.player else player.name
            
            # Count games for this player
            from db.models import Game
            games_count = Game.query.filter_by(
                tournament_id=tournament.id, 
                player_id=player.id
            ).count()
            
            print(f"  {player_name}")
            print(f"    Points: {player.points}")
            print(f"    Games: {games_count}")
            if hasattr(player, 'team_name') and player.team_name:
                print(f"    Team: {player.team_name}")
            print()
        
        # Summary statistics  
        from db.models import Game
        total_players = len(players)
        total_points = sum(p.points for p in players if p.points)
        total_games = Game.query.filter_by(tournament_id=tournament.id).count()
        
        print(f"📊 Summary:")
        print(f"  Total Players: {total_players}")
        print(f"  Total Points: {total_points}")
        print(f"  Total Games: {total_games}")
        print(f"  Average Points per Player: {total_points/total_players:.2f}")
        print(f"  Average Games per Player: {total_games/total_players:.2f}")
        
        # Verify that it's marked as a team tournament but with individual data
        if not tournament.is_team:
            print("❌ Tournament should be marked as team tournament!")
            return False
        
        if total_players < 50:  # Should have many players from multiple teams
            print(f"⚠️  Expected more players (got {total_players}), might be parsing issue")
        
        print()
        print("🎉 Team tournament test PASSED!")
        print("✅ Successfully extracted individual player data from team tournament!")
        
        return True

if __name__ == "__main__":
    success = test_team_tournament()
    sys.exit(0 if success else 1)
