import csv
import io
from flask import Blueprint, request, jsonify, abort, session
from backend.db.models import db, Player, Note
from datetime import datetime, date
from .auth import login_required, admin_required

players_bp = Blueprint('players', __name__)

@players_bp.route('/players', methods=['GET'])
@login_required
def list_players():
    active = request.args.get('active')
    query = Player.query
    if active is not None:
        if active.lower() == 'true':
            query = query.filter_by(is_active=True)
        elif active.lower() == 'false':
            query = query.filter_by(is_active=False)
    players = query.order_by(Player.last_name.asc()).all()
    return jsonify([p.to_dict() for p in players])

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
                changes.append(f"{key}: '{old_value}' → '{value}'")
                setattr(player, key, value)
    if changes:
        note_text = "Geändert: " + "; ".join(changes)
        note = Note(player=player, content=note_text, created_at=datetime.now())
        db.session.add(note)

    db.session.commit()
    return jsonify(player.to_dict())

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
        ('phone', 'Telefon', str),
        ('email', 'Email', str),
        ('club', 'Verein', str),
    ]

    for row in reader:
        # Only import Stamm-Spieler
        if row.get('Funktion', '').strip() != 'Stamm-Spieler':
            continue
        p_number = int(row.get('PNr', 0))
        player = Player.query.filter_by(p_number=p_number).first()

        # Determine female from Sex column
        is_female = bool(row.get('Sex', '').strip())

        if player:
            # Update existing player and track changes
            changes = []
            for attr, csv_key, cast in field_map:
                new_value = cast(row.get(csv_key, ''))
                old_value = getattr(player, attr)
                if old_value != new_value:
                    changes.append(f"{attr}: '{old_value}' → '{new_value}'")
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
    return jsonify([
        {
            'id': note.id,
            'content': note.content,
            'created_at': note.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
        for note in notes
    ])
