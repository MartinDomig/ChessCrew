import csv
import io
from flask import Blueprint, request, jsonify, abort, session
from db.models import db, Player, Note, TournamentPlayer, Tournament, Game
from datetime import datetime, date, timedelta
from .auth import login_required, admin_required

players_bp = Blueprint('players', __name__)

# Key translations for notes
KEY_TRANSLATIONS = {
    'first_name': 'Vorname',
    'last_name': 'Nachname',
    'elo': 'ELO',
    'fide_number': 'FIDE-Nr.',
    'fide_elo': 'FIDE-ELO',
    'birthday': 'Geburtsdatum',
    'kat': 'Kategorie',
    'zip': 'PLZ',
    'town': 'Ort',
    'country': 'Land',
    'phone': 'Telefon',
    'email': 'E-Mail',
    'club': 'Verein',
    'is_active': 'Aktiv',
    'female': 'Weiblich',
    'p_number': 'PNr',
    'tags': 'Tags',
    'rating': 'Wertung',
    'username': 'Benutzername',
    'citizen': 'Staatsbuerger',
    'address': 'Adresse',
    'fide_title': 'FIDE-Titel'
}

def format_note(note):
    """Format a note for JSON response."""
    return {
        'id': note.id,
        'content': note.content,
        'manual': note.manual,
        'created_at': note.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        'updated_at': note.updated_at.strftime('%Y-%m-%d %H:%M:%S')
    }

def format_tournament_data(tp, tournament):
    """Format tournament data for a player's tournament participation."""
    return {
        'id': tp.id,  # TournamentPlayer ID for disassociation
        'tournament_id': tournament.id,
        'tournament_name': tournament.name,
        'date': tournament.date.isoformat() if tournament.date else None,
        'location': tournament.location,
        'is_team': tournament.is_team,
        'rank': tp.ranking,
        'starting_rank': tp.starting_rank,
        'title': tp.title,
        'rating': tp.rating,
        'points': tp.points,
        'tiebreak1': tp.tiebreak1,
        'tiebreak2': tp.tiebreak2,
        'games_played': len([g for g in tournament.games if g.player_id == tp.id]),
        'total_players': len(tournament.tournament_players)
    }

@players_bp.route('/players', methods=['GET'])
@login_required
def list_players():
    """
    List all players with embedded notes and tournament data for offline support.
    This endpoint now includes:
    - Player basic info
    - Tags
    - Notes (for offline access in PlayerDetails)
    - Tournaments (for offline access in PlayerDetails) 
    - Tournament stats
    """
    active = request.args.get('active')
    query = Player.query
    
    # Filter by active status if specified
    if active is not None:
        if active.lower() == 'true':
            query = query.filter_by(is_active=True)
        elif active.lower() == 'false':
            query = query.filter_by(is_active=False)
    
    # Eager load related data to avoid N+1 queries
    players = query.options(
        db.selectinload(Player.tags),
        db.selectinload(Player.notes),
        db.selectinload(Player.tournament_players).selectinload(TournamentPlayer.tournament)
    ).order_by(Player.last_name.asc()).all()
    
    # Calculate tournament stats in batch to avoid N+1 queries
    cutoff_date = datetime.now().date() - timedelta(days=360)
    
    # Get all tournament players for active players in one query
    player_ids = [p.id for p in players]
    if player_ids:
        # Calculate points separately (no join to games to avoid duplication)
        points_query = db.session.query(
            TournamentPlayer.player_id,
            db.func.sum(db.func.coalesce(TournamentPlayer.points, 0)).label('total_points')
        ).join(
            Tournament, TournamentPlayer.tournament_id == Tournament.id
        ).filter(
            TournamentPlayer.player_id.in_(player_ids),
            Tournament.elo_rating.is_(None),
            Tournament.date >= cutoff_date
        ).group_by(TournamentPlayer.player_id).all()
        
        # Calculate games count
        games_query = db.session.query(
            TournamentPlayer.player_id,
            db.func.count(Game.id).label('total_games')
        ).select_from(TournamentPlayer).outerjoin(
            Tournament, TournamentPlayer.tournament_id == Tournament.id
        ).outerjoin(
            Game, db.and_(
                Game.tournament_id == Tournament.id,
                Game.player_id == TournamentPlayer.id
            )
        ).filter(
            TournamentPlayer.player_id.in_(player_ids),
            Tournament.date >= cutoff_date
        ).group_by(TournamentPlayer.player_id).all()

        # total games_rated and total_points_rated
        rated_points_query = db.session.query(
            TournamentPlayer.player_id,
            db.func.sum(db.func.coalesce(TournamentPlayer.points, 0)).label('total_points_rated')
        ).join(
            Tournament, TournamentPlayer.tournament_id == Tournament.id
        ).filter(
            TournamentPlayer.player_id.in_(player_ids),
            Tournament.elo_rating.isnot(None),
            Tournament.date >= cutoff_date
        ).group_by(TournamentPlayer.player_id).all()

        rated_games_query = db.session.query(
            TournamentPlayer.player_id,
            db.func.count(Game.id).label('total_games_rated')
        ).select_from(TournamentPlayer).outerjoin(
            Tournament, TournamentPlayer.tournament_id == Tournament.id
        ).outerjoin(
            Game, db.and_(
                Game.tournament_id == Tournament.id,
                Game.player_id == TournamentPlayer.id
            )
        ).filter(
            TournamentPlayer.player_id.in_(player_ids),
            Tournament.elo_rating.isnot(None),
            Tournament.date >= cutoff_date
        ).group_by(TournamentPlayer.player_id).all()

        # Convert to dict for easy lookup
        points_dict = {stat.player_id: stat.total_points or 0 for stat in points_query}
        games_dict = {stat.player_id: stat.total_games or 0 for stat in games_query}
        rated_points_dict = {stat.player_id: stat.total_points_rated or 0 for stat in rated_points_query}
        rated_games_dict = {stat.player_id: stat.total_games_rated or 0 for stat in rated_games_query}

        tournament_stats = {}
        for player_id in player_ids:
            tournament_stats[player_id] = {
                'total_points': points_dict.get(player_id, 0),
                'total_games': games_dict.get(player_id, 0),
                'total_points_rated': rated_points_dict.get(player_id, 0),
                'total_games_rated': rated_games_dict.get(player_id, 0)
            }
    else:
        tournament_stats = {}
    
    return jsonify([
        {
            **p.to_dict(),
            'tags': [{'id': t.id, 'name': t.name, 'color': t.color} for t in p.tags],
            'notes': [format_note(note) for note in p.notes],
            'tournaments': [
                format_tournament_data(tp, tp.tournament)
                for tp in sorted(p.tournament_players, 
                               key=lambda tp: tp.tournament.date if tp.tournament else datetime.min.date(), 
                               reverse=True)
            ],
            'tournament_stats': tournament_stats.get(p.id, {'total_points': 0, 'total_games': 0})
        }
        for p in players
    ])

@players_bp.route('/players', methods=['POST'])
@login_required
def create_player():
    data = request.get_json()
    username = data.get('username')
    rating = data.get('rating')
    if not username:
        return jsonify({'error': 'Username required'}), 400
    if Player.query.filter_by(username=username).first():
        return jsonify({'error': 'Player exists'}), 409
    player = Player(username=username, rating=rating)
    db.session.add(player)
    db.session.commit()
    return jsonify({'id': player.id, 'username': player.username, 'rating': player.rating}), 201

# Get a single player by ID (including tags, notes, and tournaments)
@players_bp.route('/players/<int:player_id>', methods=['GET'])
@login_required
def get_player(player_id):
    # Use eager loading to avoid N+1 queries
    player = Player.query.options(
        db.selectinload(Player.tags),
        db.selectinload(Player.notes),
        db.selectinload(Player.tournament_players).selectinload(TournamentPlayer.tournament)
    ).get(player_id)
    
    if not player:
        return jsonify({'error': 'Player not found'}), 404
    
    # Calculate tournament stats using separate queries to avoid duplication
    cutoff_date = datetime.now().date() - timedelta(days=360)
    
    # Calculate points
    points_query = db.session.query(
        db.func.sum(db.func.coalesce(TournamentPlayer.points, 0)).label('total_points')
    ).join(
        Tournament, TournamentPlayer.tournament_id == Tournament.id
    ).filter(
        TournamentPlayer.player_id == player_id,
        Tournament.date >= cutoff_date
    ).first()
    
    # Calculate games
    games_query = db.session.query(
        db.func.count(Game.id).label('total_games')
    ).select_from(TournamentPlayer).outerjoin(
        Tournament, TournamentPlayer.tournament_id == Tournament.id
    ).outerjoin(
        Game, db.and_(
            Game.tournament_id == Tournament.id,
            Game.player_id == TournamentPlayer.id
        )
    ).filter(
        TournamentPlayer.player_id == player_id,
        Tournament.date >= cutoff_date
    ).first()
    
    tournament_stats = {
        'total_points': points_query.total_points or 0,
        'total_games': games_query.total_games or 0
    }
    
    return jsonify({
        **player.to_dict(),
        'tags': [{'id': t.id, 'name': t.name, 'color': t.color} for t in player.tags],
        'notes': [format_note(note) for note in player.notes],
        'tournaments': [
            format_tournament_data(tp, tp.tournament)
            for tp in sorted(player.tournament_players, 
                           key=lambda tp: tp.tournament.date if tp.tournament else datetime.min.date(), 
                           reverse=True)
        ],
        'tournament_stats': tournament_stats
    })

@players_bp.route('/players/<int:player_id>', methods=['PUT', 'PATCH'])
@login_required
def update_player(player_id):
    player = Player.query.get(player_id)
    if not player:
        return jsonify({'error': 'Player not found'}), 404
    data = request.get_json()

    allowed_fields = set(player.to_dict().keys())
    changes = []
    for key, value in data.items():
        if key in allowed_fields:
            old_value = getattr(player, key)
            if old_value != value:
                key_label = KEY_TRANSLATIONS.get(key, key)
                changes.append(f"{key_label}: '{old_value}' → '{value}'")
                setattr(player, key, value)
    if changes:
        note_text = "Geändert: " + "; ".join(changes)
        note = Note(player=player, content=note_text, created_at=datetime.now())
        db.session.add(note)

    db.session.commit()
    
    # Calculate tournament stats using optimized query
    cutoff_date = datetime.now().date() - timedelta(days=360)
    tournament_stats_query = db.session.query(
        db.func.sum(db.func.coalesce(TournamentPlayer.points, 0)).label('total_points'),
        db.func.count(Game.id).label('total_games')
    ).outerjoin(
        Tournament, TournamentPlayer.tournament_id == Tournament.id
    ).outerjoin(
        Game, db.and_(
            Game.tournament_id == Tournament.id,
            Game.player_id == TournamentPlayer.id
        )
    ).filter(
        TournamentPlayer.player_id == player_id,
        Tournament.date >= cutoff_date
    ).first()
    
    tournament_stats = {
        'total_points': tournament_stats_query.total_points or 0,
        'total_games': tournament_stats_query.total_games or 0
    }
    
    return jsonify({
        **player.to_dict(),
        'tournament_stats': tournament_stats
    })

@players_bp.route('/players/<int:player_id>', methods=['DELETE'])
@login_required
def delete_player(player_id):
    player = Player.query.get(player_id)
    if not player:
        return jsonify({'error': 'Player not found'}), 404
    db.session.delete(player)
    db.session.commit()
    return jsonify({'status': 'deleted'})

def parse_birthday(s):
    s = s.strip()
    if not s:
        return None
    # Accept formats: YYYYMMDD or YYYY-MM-DD
    try:
        if '-' in s:
            return date.fromisoformat(s)
        elif len(s) == 8:
            return date(int(s[:4]), int(s[4:6]), int(s[6:8]))
    except Exception:
        return None
    return None

@players_bp.route('/players-import-csv', methods=['POST'])
@admin_required
def import_players_csv():
    if 'file' not in request.files:
        print("No file uploaded")
        return jsonify({'error': 'No file uploaded'}), 400
    file = request.files['file']
    if not file.filename.endswith('.csv'):
        return jsonify({'error': 'Invalid file type'}), 400
    file.seek(0, 2)  # Move to end of file
    size = file.tell()
    file.seek(0)  # Reset to start
    if size > 2 * 1024 * 1024:
        return jsonify({'error': 'File too large (max 2MB)'}), 400
    
    stream = io.StringIO(file.stream.read().decode('utf-8'))
    reader = csv.DictReader(stream, delimiter=';')
    required_headers = [
        'PNr', 'Vorname', 'Nachname', 'elo', 'Funktion', 'Verein', 'Staat', 'Gebdat', 'Sex'
    ]
    missing = [h for h in required_headers if h not in reader.fieldnames]
    if missing:
        return jsonify({'error': f'Missing required headers: {", ".join(missing)}'}), 400
    imported = 0
   
    # Define mapping from CSV to Player fields
    field_map = [
        ('first_name', 'Vorname', str),
        ('last_name', 'Nachname', str),
        ('elo', 'elo', int),
        ('fide_number', 'FideNr', lambda v: int(v) if v else None),
        ('fide_elo', 'FideElo', lambda v: int(v) if v else None),
        ('birthday', 'Gebdat', parse_birthday),
        ('kat', 'Kategorie', str),
        ('zip', 'Plz', str),
        ('town', 'Ort', str),
        ('country', 'Staat', str),
        ('citizen', 'Staatsbuerger', str),
        ('phone', 'Telefon', str),
        ('email', 'Email', str),
        ('club', 'Verein', str),
        ('address', 'Adresse', str),
        ('fide_title', 'fidetitel', str)
    ]

    for row in reader:
        # Only import Stamm-Spieler
        if row.get('Funktion', '').strip() != 'Stamm-Spieler':
            continue
        
        # Determine is_active from bis column
        bis_str = row.get('bis', '').strip()
        is_active = None
        if bis_str:
            try:
                bis_date = datetime.strptime(bis_str, '%d.%m.%Y').date()
                if bis_date < date.today():
                    is_active = False
            except Exception:
                pass
        
        p_number = int(row.get('PNr', 0))
        player = Player.query.filter_by(p_number=p_number).first()

        # Determine female from Sex column
        sex_value = row.get('Sex', '').strip().lower()
        is_female = sex_value in ('w', 'f')

        # Normalize names: some names are entered in all UPPERCASE.
        for key in ['Vorname', 'Nachname', 'Verein', 'Ort', 'Staat', 'Adresse']:
            if key in row:
                row[key] = row[key].strip().title()

        if player:
            # Update existing player and track changes
            changes = []

            if is_active is not None and player.is_active != is_active:
                changes.append(f"Aktiv: '{player.is_active}' → '{is_active}'")
                player.is_active = is_active
            
            for attr, csv_key, cast in field_map:
                new_value = cast(row.get(csv_key, ''))
                old_value = getattr(player, attr)
                if old_value != new_value:
                    key_label = KEY_TRANSLATIONS.get(attr, attr)
                    changes.append(f"{key_label}: '{old_value}' → '{new_value}'")
                    setattr(player, attr, new_value)
            note_text = "Importiert"
            if changes:
                note_text += ": " + "; ".join(changes)
            note = Note(player=player, content=note_text, created_at=datetime.now())
            db.session.add(note)
            
        else:
            # Create new player
            player = Player(
                p_number=p_number,
                **{attr: cast(row.get(csv_key, '')) for attr, csv_key, cast in field_map},
                is_active=False,
                female=is_female
            )
            db.session.add(player)
            note = Note(player=player, content="Importiert", created_at=datetime.now())
            db.session.add(note)
            imported += 1
    
    db.session.commit()
    return jsonify({'imported': imported}), 201

@players_bp.route('/players/<int:player_id>/notes', methods=['GET'])
@login_required
def get_player_notes(player_id):
    player = Player.query.get(player_id)
    if not player:
        return jsonify({'error': 'Player not found'}), 404
    notes = Note.query.filter_by(player_id=player.id).order_by(Note.created_at.desc()).all()
    return jsonify([format_note(note) for note in notes])

@players_bp.route('/players/<int:player_id>/notes', methods=['POST'])
@login_required
def create_player_note(player_id):
    player = Player.query.get(player_id)
    if not player:
        return jsonify({'error': 'Player not found'}), 404
    data = request.get_json(force=True)
    content = data.get('content')
    if not content:
        return jsonify({'error': 'Content is required'}), 400
    note = Note(player=player, content=content, manual=True, created_at=datetime.now())
    db.session.add(note)
    db.session.commit()
    return jsonify(format_note(note)), 201

@players_bp.route('/players/<int:player_id>/notes/<int:note_id>', methods=['PUT', 'PATCH'])
@login_required
def update_player_note(player_id, note_id):
    player = Player.query.get(player_id)
    if not player:
        return jsonify({'error': 'Player not found'}), 404
    note = Note.query.get(note_id)
    if not note:
        return jsonify({'error': 'Note not found'}), 404
    data = request.get_json(force=True)
    content = data.get('content')
    if not content:
        return jsonify({'error': 'Content is required'}), 400
    note.content = content
    note.updated_at = datetime.now()
    db.session.commit()
    return jsonify(format_note(note)), 200

@players_bp.route('/players/<int:player_id>/notes/<int:note_id>', methods=['DELETE'])
@login_required
def delete_player_note(player_id, note_id):
    player = Player.query.get(player_id)
    if not player:
        return jsonify({'error': 'Player not found'}), 404
    note = Note.query.get(note_id)
    if not note:
        return jsonify({'error': 'Note not found'}), 404
    db.session.delete(note)
    db.session.commit()
    return jsonify({'message': 'Note deleted successfully'}), 200

@players_bp.route('/players/<int:player_id>/tournaments', methods=['GET'])
@login_required
def get_player_tournaments(player_id):
    player = Player.query.get(player_id)
    if not player:
        return jsonify({'error': 'Player not found'}), 404
    
    # Get all tournament participations for this player
    tournament_players = db.session.query(TournamentPlayer, Tournament)\
        .join(Tournament, TournamentPlayer.tournament_id == Tournament.id)\
        .filter(TournamentPlayer.player_id == player_id)\
        .order_by(Tournament.date.desc())\
        .all()
    
    return jsonify([
        format_tournament_data(tp, tournament)
        for tp, tournament in tournament_players
    ])
