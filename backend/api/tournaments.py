import csv
import io
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
    tournaments = Tournament.query.all()
    return jsonify([{'id': t.id, 'name': t.name} for t in tournaments])

@tournaments_bp.route('/tournaments/<int:tournament_id>', methods=['GET'])
def get_tournament(tournament_id):
    t = Tournament.query.get_or_404(tournament_id)
    return jsonify({'id': t.id, 'name': t.name})

@tournaments_bp.route('/tournaments', methods=['POST'])
@admin_required
def create_tournament():
    data = request.json
    t = Tournament(name=data['name'])
    db.session.add(t)
    db.session.commit()
    return jsonify({'id': t.id, 'name': t.name}), 201

@tournaments_bp.route('/tournaments/<int:tournament_id>', methods=['PUT'])
@admin_required
def update_tournament(tournament_id):
    t = Tournament.query.get_or_404(tournament_id)
    data = request.json
    t.name = data.get('name', t.name)
    db.session.commit()
    return jsonify({'id': t.id, 'name': t.name})

@tournaments_bp.route('/tournaments/<int:tournament_id>', methods=['DELETE'])
@admin_required
def delete_tournament(tournament_id):
    t = Tournament.query.get_or_404(tournament_id)
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
            'player_name': tp.player_name,
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
        'player_name': tp.player_name,
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
        player_name=data.get('player_name'),
        rank=data.get('rank'),
        points=data.get('points'),
        tiebreak1=data.get('tiebreak1'),
        tiebreak2=data.get('tiebreak2')
    )
    db.session.add(tp)
    db.session.commit()
    return jsonify({'player_id': tp.player_id, 'player_name': tp.player_name}), 201

@tournaments_bp.route('/tournaments/<int:tournament_id>/players/<int:player_id>', methods=['PUT'])
@admin_required
def update_tournament_player(tournament_id, player_id):
    tp = TournamentPlayer.query.filter_by(tournament_id=tournament_id, player_id=player_id).first_or_404()
    data = request.json
    tp.rank = data.get('rank', tp.rank)
    tp.points = data.get('points', tp.points)
    tp.tiebreak1 = data.get('tiebreak1', tp.tiebreak1)
    tp.tiebreak2 = data.get('tiebreak2', tp.tiebreak2)
    tp.player_name = data.get('player_name', tp.player_name)
    db.session.commit()
    return jsonify({'player_id': tp.player_id, 'player_name': tp.player_name})

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
            'white_player_id': g.white_player_id,
            'black_player_id': g.black_player_id,
            'result': g.result,
            'moves': g.moves
        } for g in games
    ])

@tournaments_bp.route('/tournaments/<int:tournament_id>/games/<int:game_id>', methods=['GET'])
def get_game(tournament_id, game_id):
    g = Game.query.filter_by(tournament_id=tournament_id, id=game_id).first_or_404()
    return jsonify({
        'id': g.id,
        'white_player_id': g.white_player_id,
        'black_player_id': g.black_player_id,
        'result': g.result,
        'moves': g.moves
    })

@tournaments_bp.route('/tournaments/<int:tournament_id>/games', methods=['POST'])
@admin_required
def create_game(tournament_id):
    data = request.json
    g = Game(
        tournament_id=tournament_id,
        white_player_id=data['white_player_id'],
        black_player_id=data['black_player_id'],
        result=data['result'],
        moves=data['moves']
    )
    db.session.add(g)
    db.session.commit()
    return jsonify({'id': g.id}), 201

@tournaments_bp.route('/tournaments/<int:tournament_id>/games/<int:game_id>', methods=['PUT'])
@admin_required
def update_game(tournament_id, game_id):
    g = Game.query.filter_by(tournament_id=tournament_id, id=game_id).first_or_404()
    data = request.json
    g.white_player_id = data.get('white_player_id', g.white_player_id)
    g.black_player_id = data.get('black_player_id', g.black_player_id)
    g.result = data.get('result', g.result)
    g.moves = data.get('moves', g.moves)
    db.session.commit()
    return jsonify({'id': g.id})

@tournaments_bp.route('/tournaments/<int:tournament_id>/games/<int:game_id>', methods=['DELETE'])
@admin_required
def delete_game(tournament_id, game_id):
    g = Game.query.filter_by(tournament_id=tournament_id, id=game_id).first_or_404()
    db.session.delete(g)
    db.session.commit()
    return '', 204

@tournaments_bp.route('/tournaments-import-xlsx', methods=['POST'])
@admin_required
def import_tournaments_xlsx():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    file = request.files['file']
    if not file.filename.endswith('.xlsx'):
        return jsonify({'error': 'Invalid file type'}), 400
    # Save file to temp location
    with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
        file.save(tmp.name)
        tmp_path = tmp.name
    try:
        # Read the xlsx file
        df = pd.read_excel(tmp_path)
        # TODO: Adjust parsing logic for your file format
        # Example: Assume columns 'Tournament', 'Player', 'Rank', 'Points', 'Tiebreak1', 'Tiebreak2', 'GameWhite', 'GameBlack', 'Result', 'Moves'
        tournament_name = df['Tournament'][0] if 'Tournament' in df.columns else 'Imported Tournament'
        tournament = Tournament(name=tournament_name)
        db.session.add(tournament)
        db.session.commit()
        for _, row in df.iterrows():
            # Add TournamentPlayer
            tp = TournamentPlayer(
                tournament_id=tournament.id,
                player_name=row.get('Player'),
                rank=row.get('Rank'),
                points=row.get('Points'),
                tiebreak1=row.get('Tiebreak1'),
                tiebreak2=row.get('Tiebreak2')
            )
            db.session.add(tp)
            # Add Game if present
            if row.get('GameWhite') and row.get('GameBlack'):
                game = Game(
                    tournament_id=tournament.id,
                    white_player_id=None,  # You may want to resolve player IDs
                    black_player_id=None,
                    result=row.get('Result'),
                    moves=row.get('Moves')
                )
                db.session.add(game)
        db.session.commit()
        return jsonify({'imported': True, 'tournament_id': tournament.id}), 201
    finally:
        os.remove(tmp_path)

