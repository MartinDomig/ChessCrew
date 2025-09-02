import csv
import hashlib
import io
import re
import os
import tempfile
import pandas as pd
from flask import Blueprint, request, jsonify, abort, session
from backend.db.models import db, Player, Note, Tournament, TournamentPlayer, Game
from datetime import datetime, date
from .auth import login_required, admin_required

tournaments_bp = Blueprint('tournaments', __name__)

# --- Tournament Endpoints ---
@tournaments_bp.route('/tournaments', methods=['GET'])
def list_tournaments():
    tournaments = Tournament.query.order_by(Tournament.date.desc()).all()
    return jsonify([{'id': t.id, 'name': t.name, 'date': t.date, 'location': t.location} for t in tournaments])

@tournaments_bp.route('/tournaments/<int:tournament_id>', methods=['GET'])
def get_tournament(tournament_id):
    t = Tournament.query.get_or_404(tournament_id)
    return jsonify({'id': t.id, 'name': t.name, 'date': t.date, 'location': t.location})

@tournaments_bp.route('/tournaments', methods=['POST'])
@admin_required
def create_tournament():
    data = request.json
    t = Tournament(name=data['name'])
    db.session.add(t)
    db.session.commit()
    return jsonify({'id': t.id, 'name': t.name, 'date': t.date, 'location': t.location}), 201

@tournaments_bp.route('/tournaments/<int:tournament_id>', methods=['PUT'])
@admin_required
def update_tournament(tournament_id):
    t = Tournament.query.get_or_404(tournament_id)
    data = request.json
    t.name = data.get('name', t.name)
    
    # Parse date string to date object if provided
    if 'date' in data and data['date']:
        try:
            t.date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format. Expected YYYY-MM-DD'}), 400
    
    t.location = data.get('location', t.location)
    db.session.commit()
    return jsonify({'id': t.id, 'name': t.name, 'date': t.date, 'location': t.location})

@tournaments_bp.route('/tournaments/<int:tournament_id>', methods=['DELETE'])
@admin_required
def delete_tournament(tournament_id):
    t = Tournament.query.options(db.joinedload(Tournament.tournament_players), db.joinedload(Tournament.games)).get_or_404(tournament_id)
    db.session.delete(t)
    db.session.commit()
    return '', 204

# --- TournamentPlayer Endpoints ---
@tournaments_bp.route('/tournaments/<int:tournament_id>/players', methods=['GET'])
def list_tournament_players(tournament_id):
    players = TournamentPlayer.query.filter_by(tournament_id=tournament_id).all()
    return jsonify([
        {
            'player_id': tp.player_id,
            'name': tp.name,
            'rank': tp.rank,
            'points': tp.points,
            'tiebreak1': tp.tiebreak1,
            'tiebreak2': tp.tiebreak2
        } for tp in players
    ])

@tournaments_bp.route('/tournaments/<int:tournament_id>/players/<int:player_id>', methods=['GET'])
def get_tournament_player(tournament_id, player_id):
    tp = TournamentPlayer.query.filter_by(tournament_id=tournament_id, player_id=player_id).first_or_404()
    return jsonify({
        'player_id': tp.player_id,
        'name': tp.name,
        'rank': tp.rank,
        'points': tp.points,
        'tiebreak1': tp.tiebreak1,
        'tiebreak2': tp.tiebreak2
    })

@tournaments_bp.route('/tournaments/<int:tournament_id>/players', methods=['POST'])
@admin_required
def create_tournament_player(tournament_id):
    data = request.json
    tp = TournamentPlayer(
        tournament_id=tournament_id,
        player_id=data.get('player_id'),
        name=data.get('name'),
        rank=data.get('rank'),
        points=data.get('points'),
        tiebreak1=data.get('tiebreak1'),
        tiebreak2=data.get('tiebreak2')
    )
    db.session.add(tp)
    db.session.commit()
    return jsonify({'player_id': tp.player_id, 'name': tp.name}), 201

@tournaments_bp.route('/tournaments/<int:tournament_id>/players/<int:player_id>', methods=['PUT'])
@admin_required
def update_tournament_player(tournament_id, player_id):
    tp = TournamentPlayer.query.filter_by(tournament_id=tournament_id, player_id=player_id).first_or_404()
    data = request.json
    tp.rank = data.get('rank', tp.rank)
    tp.points = data.get('points', tp.points)
    tp.tiebreak1 = data.get('tiebreak1', tp.tiebreak1)
    tp.tiebreak2 = data.get('tiebreak2', tp.tiebreak2)
    tp.name = data.get('name', tp.name)
    db.session.commit()
    return jsonify({'player_id': tp.player_id, 'name': tp.name})

@tournaments_bp.route('/tournaments/<int:tournament_id>/players/<int:player_id>', methods=['DELETE'])
@admin_required
def delete_tournament_player(tournament_id, player_id):
    tp = TournamentPlayer.query.filter_by(tournament_id=tournament_id, player_id=player_id).first_or_404()
    db.session.delete(tp)
    db.session.commit()
    return '', 204

# --- Game Endpoints ---
@tournaments_bp.route('/tournaments/<int:tournament_id>/games', methods=['GET'])
def list_games(tournament_id):
    games = Game.query.filter_by(tournament_id=tournament_id).all()
    return jsonify([
        {
            'id': g.id,
            'tournament_id': g.tournament_id,
            'player_id': g.player_id,
            'opponent_id': g.opponent_id,
            'player_color': g.player_color,
            'result': g.result,
            'round_number': g.round_number,
            'pgn': g.pgn
        } for g in games
    ])

@tournaments_bp.route('/tournaments/<int:tournament_id>/games/<int:game_id>', methods=['GET'])
def get_game(tournament_id, game_id):
    g = Game.query.filter_by(tournament_id=tournament_id, id=game_id).first_or_404()
    return jsonify({
            'id': g.id,
            'tournament_id': g.tournament_id,
            'player_id': g.player_id,
            'opponent_id': g.opponent_id,
            'player_color': g.player_color,
            'result': g.result,
            'round_number': g.round_number,
            'pgn': g.pgn
    })

@tournaments_bp.route('/tournaments/<int:tournament_id>/games', methods=['POST'])
@admin_required
def create_game(tournament_id):
    data = request.json
    g = Game(
        tournament_id=tournament_id,
        player_id=data['player_id'],
        opponent_id=data['opponent_id'],
        player_color=data['player_color'],
        result=data['result'],
        round_number=data['round_number'],
        pgn=data['pgn']
    )
    db.session.add(g)
    db.session.commit()
    return jsonify({'id': g.id}), 201

@tournaments_bp.route('/tournaments/<int:tournament_id>/games/<int:game_id>', methods=['PUT'])
@admin_required
def update_game(tournament_id, game_id):
    g = Game.query.filter_by(tournament_id=tournament_id, id=game_id).first_or_404()
    data = request.json
    g.player_id = data.get('player_id', g.player_id)
    g.opponent_id = data.get('opponent_id', g.opponent_id)
    g.player_color = data.get('player_color', g.player_color)
    g.result = data.get('result', g.result)
    g.round_number = data.get('round_number', g.round_number)
    g.pgn = data.get('pgn', g.pgn)
    db.session.commit()
    return jsonify({'id': g.id})

@tournaments_bp.route('/tournaments/<int:tournament_id>/games/<int:game_id>', methods=['DELETE'])
@admin_required
def delete_game(tournament_id, game_id):
    g = Game.query.filter_by(tournament_id=tournament_id, id=game_id).first_or_404()
    db.session.delete(g)
    db.session.commit()
    return '', 204

def find_existing_player(name, shuffling=False):
    name = name.strip()
    if not name:
        return None
    if ',' in name:
        last, first = [n.strip() for n in name.split(',', 1)]
    else:
        parts = name.split()
        if len(parts) == 2:
            first, last = parts
        elif len(parts) > 2:
            first = parts[0]
            last = ' '.join(parts[1:])
        else:
            first = name
            last = ''
    # Lookup 1: Lastname Firstname
    player = Player.query.filter(
        db.func.lower(Player.first_name) == first.lower(),
        db.func.lower(Player.last_name) == last.lower()
    ).first()
    if player:
        return player
    # Lookup 2: Firstname Lastname
    player = Player.query.filter(
        db.func.lower(Player.first_name) == last.lower(),
        db.func.lower(Player.last_name) == first.lower()
    ).first()
    if player:
        return player

    # if name contains Ae, ae, Oe, oe, Ue, ue replace with umlauts and try again
    name_with_umlauts = name.lower().replace('ae', 'ä').replace('oe', 'ö').replace('ue', 'ü').replace('sz', 'ß')
    if name_with_umlauts != name.lower():
        player = find_existing_player(name_with_umlauts)
        if player:
            return player
    
    if not shuffling:
        # shuffle name parts: move the first part to the last
        name_parts = name.split()
        for i in range(len(name_parts)):
            shuffled_name = ' '.join(name_parts[i:] + name_parts[:i])
            player = find_existing_player(shuffled_name, shuffling=True)
            if player:
                return player

    return None

def parse_tournament_metadata(df, request):
    # Tournament name is always on the second line (index 1)
    second_row = df.iloc[1]
    values = [str(v).strip() for v in second_row if pd.notnull(v)]
    if len(values) == 1:
        tournament_name = values[0].strip()
    else:
        raise ValueError("No tournament name found")

    location = request.form.get('location')
    date = None

    # Exports can contain tournament details. If they do, we will have a line for each detail:
    if not location:
        for idx, row in df.iterrows():
            if isinstance(row.values[0], str) and row.values[0].startswith('Ort :'):
                location = row.values[0].split(':', 1)[1].strip()
    for idx, row in df.iterrows():
        if isinstance(row.values[0], str) and row.values[0].startswith('Datum :'):
            date = row.values[0].split(':', 1)[1].strip()
            date = datetime.strptime(date, '%d.%m.%Y').date() if date else None

    if not date:
        date_str = request.form.get('date')
        date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else None
    if not date:
        raise ValueError("No tournament date given")

    return tournament_name, location, date

def find_header_row(df):
    for idx, row in df.iterrows():
        values = [str(v).strip() for v in row]
        if 'Name' in values:
            return idx
    raise ValueError("Header row not found")

def detect_round_columns(header):
    round_columns = []
    for col in header:
        if '1' in col:
            round_columns.append(col)
            break
    if not round_columns:
        raise ValueError("No column found for first round")

    first_round_column = round_columns[0]
    i = 2
    while True:
        next_round_column = first_round_column.replace('1', str(i))
        if next_round_column in header:
            round_columns.append(next_round_column)
            i += 1
        else:
            break
    return round_columns

def parse_players(df, header, header_row_idx, tournament, find_existing_player):
    # first column after rounds contains wtg1
    round_columns = detect_round_columns(header)
    wtg1_column = header[header.index(round_columns[-1]) + 1] if round_columns else None
    if not wtg1_column:
        raise ValueError("No column found for Wtg1")
    wtg2_column = header[header.index(round_columns[-1]) + 2] if round_columns else None
    if not wtg2_column:
        raise ValueError("No column found for Wtg2")
    wtg3_column = header[header.index(round_columns[-1]) + 3] if round_columns else None

    result_format = None
    ranked_players = []
    rank = 1

    for i in range(header_row_idx + 1, len(df)):
        row = [str(v).strip() for v in df.iloc[i]]
        if not row:
            break
        data = dict(zip(header, [str(v).strip() for v in row]))
        if not data.get('Name', '') or data.get('Name', '') == "nan":
            break

        name = data.get('Name', '').strip()
        player = find_existing_player(name)
        if player:
            player.is_active = True
            db.session.add(player)
        else:
            print('Player not found:', name)

        if data.get(header[0]) != "nan":
            rank = int(data.get(header[0], 0))

        tp = TournamentPlayer(
            tournament_id=tournament.id,
            player_id=player.id if player else None,
            name=name,
            rank=rank,
            points=float(data.get(wtg1_column, 0)),
            tiebreak1=float(data.get(wtg2_column, 0)),
            tiebreak2=float(data.get(wtg3_column, 0))
        )
        ranked_players.append(tp)
        db.session.add(tp)

        if result_format is None:
            for r in round_columns:
                round_result = data.get(r)
                if re.match(r'^\d+[wsb][10½+]$', round_result):
                    result_format = 'complex'
                    break
            if result_format is None:
                result_format = 'simple'
            print("Detected result format:", result_format)

    if not ranked_players:
        raise ValueError('No valid player data found')

    return ranked_players, result_format, round_columns

def parse_games(df, header, header_row_idx, round_columns, ranked_players, tournament, result_format):
    imported_games = 0
    rank = 0
    for i in range(header_row_idx + 1, len(df)):
        row = [str(v).strip() for v in df.iloc[i]]
        if not row:
            break
        data = dict(zip(header, [str(v).strip() for v in row]))
        if not data.get('Name', '') or data.get('Name', '') == "nan":
            break

        rank += 1
        player = ranked_players[rank - 1]
        if not player:
            raise ValueError(f'Player not found: {data.get(header[0], 0)}')

        for r in range(len(round_columns)):
            round_result = data.get(round_columns[r])
            if round_result == '*':
                continue

            player_color = None
            opponent = None
            result = None

            if result_format == 'simple':
                opponent = ranked_players[int(r)]
                result = round_result
            else:
                m = re.match(r'^(\d+)([wsb])([10½+])$', round_result)
                if not m:
                    print(f'Invalid round result, assuming skip: {round_result} for {player.name}')
                    continue
                opponent_nr = int(m.group(1))
                opponent = ranked_players[opponent_nr - 1]
                result = m.group(3)
                color = m.group(2)
                if color == 'w':
                    player_color = 'white'
                elif color in ['s', 'b']:
                    player_color = 'black'

            if not opponent:
                raise ValueError(f'Invalid opponent: {round_result} for {player.name}')
            if player.id == opponent.id:
                raise ValueError(f'Player cannot play against themselves: {player.name}')
            if not result:
                raise ValueError(f'Invalid round result: {round_result} for {player.name}')

            game = Game(
                tournament_id=tournament.id,
                player_id=player.id,
                player_color=player_color,
                opponent_id=opponent.id,
                round_number=r + 1,
                result=result
            )
            db.session.add(game)
            imported_games += 1

    return imported_games

@tournaments_bp.route('/tournaments-import-xlsx', methods=['POST'])
@admin_required
def import_tournaments_xlsx():
    if 'file' not in request.files:
        print("No file uploaded")
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    if not file.filename.endswith('.xlsx'):
        print("Invalid file type")
        return jsonify({'error': 'Invalid file type'}), 400

    with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
        file.save(tmp.name)
        tmp_path = tmp.name

    # create a sha256 checksum of the result file
    sha256 = hashlib.sha256()
    with open(tmp_path, 'rb') as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    checksum = sha256.hexdigest()

    # abort if a tournament with the same checksum already exists
    if Tournament.query.filter_by(checksum=checksum).first():
        return jsonify({'error': 'Tournament already imported'}), 400

    try:
        df = pd.read_excel(tmp_path, header=None)
        
        tournament_name, location, date = parse_tournament_metadata(df, request)
        
        header_row_idx = find_header_row(df)
        header = [str(v).strip() for v in df.iloc[header_row_idx]]
        if not header:
            raise ValueError("No valid header found")

        # Create tournament
        print("Creating tournament:", tournament_name)
        tournament = Tournament(name=tournament_name, checksum=checksum, date=date, location=location)
        db.session.add(tournament)
        db.session.flush()

        ranked_players, result_format, round_columns = parse_players(df, header, header_row_idx, tournament, find_existing_player)
        
        db.session.flush()
        for p in ranked_players:
            print("Ranked Player: {} - {} (ID: {})".format(p.rank, p.name, p.player_id))

        imported_games = parse_games(df, header, header_row_idx, round_columns, ranked_players, tournament, result_format)

        db.session.commit()

    except Exception as e:
        print("Import error:", e)
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

    finally:
        os.remove(tmp_path)

    return jsonify({'imported': imported_games, 'success': True}), 200

