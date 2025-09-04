import csv
import hashlib
import io
import re
import os
import tempfile
import pandas as pd
from flask import Blueprint, request, jsonify, abort, session
from db.models import db, Player, Note, Tournament, TournamentPlayer, Game
from datetime import datetime, date
from .auth import login_required, admin_required

tournaments_bp = Blueprint('tournaments', __name__)

def format_tournament_player(tp):
    """Helper function to format tournament player data consistently"""
    return {
        'player_id': tp.player_id,
        'name': tp.name,
        'rank': tp.rank,
        'points': tp.points,
        'tiebreak1': tp.tiebreak1,
        'tiebreak2': tp.tiebreak2,
        'player': {
            'id': tp.player.id,
            'first_name': tp.player.first_name,
            'last_name': tp.player.last_name,
            'kat': tp.player.kat,
            'birthday': tp.player.birthday.isoformat() if tp.player.birthday else None
        } if tp.player else None
    }

# --- Tournament Endpoints ---
@tournaments_bp.route('/tournaments', methods=['GET'])
def list_tournaments():
    tournaments = Tournament.query.order_by(Tournament.date.desc()).all()
    return jsonify([{'id': t.id, 'name': t.name, 'date': t.date, 'location': t.location, 'is_team': t.is_team} for t in tournaments])

@tournaments_bp.route('/tournaments/<int:tournament_id>', methods=['GET'])
def get_tournament(tournament_id):
    t = Tournament.query.get_or_404(tournament_id)
    return jsonify({'id': t.id, 'name': t.name, 'date': t.date, 'location': t.location, 'is_team': t.is_team})

@tournaments_bp.route('/tournaments', methods=['POST'])
@admin_required
def create_tournament():
    data = request.json
    t = Tournament(
        name=data['name'],
        is_team=data.get('is_team', False)
    )
    db.session.add(t)
    db.session.commit()
    return jsonify({'id': t.id, 'name': t.name, 'date': t.date, 'location': t.location, 'is_team': t.is_team}), 201

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
    t.is_team = data.get('is_team', t.is_team)
    db.session.commit()
    return jsonify({'id': t.id, 'name': t.name, 'date': t.date, 'location': t.location, 'is_team': t.is_team})

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
    players = TournamentPlayer.query.filter_by(tournament_id=tournament_id).options(db.joinedload(TournamentPlayer.player)).all()
    return jsonify([format_tournament_player(tp) for tp in players])

@tournaments_bp.route('/tournaments/<int:tournament_id>/players/<int:player_id>', methods=['GET'])
def get_tournament_player(tournament_id, player_id):
    tp = TournamentPlayer.query.filter_by(tournament_id=tournament_id, player_id=player_id).options(db.joinedload(TournamentPlayer.player)).first_or_404()
    return jsonify(format_tournament_player(tp))

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

@tournaments_bp.route('/tournament-players/<int:tp_id>/disassociate', methods=['PUT'])
@admin_required
def disassociate_player_from_tournament(tp_id):
    """Disassociate a player from a tournament by setting player_id to null"""
    tp = TournamentPlayer.query.get_or_404(tp_id)
    
    # Store the current player_id for response
    old_player_id = tp.player_id
    
    # Set player_id to null to disassociate
    tp.player_id = None
    db.session.commit()
    
    return jsonify({
        'id': tp.id,
        'tournament_id': tp.tournament_id,
        'old_player_id': old_player_id,
        'message': 'Player disassociated from tournament'
    })

# --- Crawler Endpoints ---
@tournaments_bp.route('/crawler/run', methods=['POST'])
@admin_required
def run_crawler():
    """Manually trigger the chess results crawler"""
    try:
        from chess_results_crawler import run_crawler
        
        # Run the crawler
        processed_count = run_crawler()
        
        return jsonify({
            'success': True,
            'message': f'Crawler completed successfully. Processed {processed_count} tournaments',
            'processed_count': processed_count
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Crawler failed: {str(e)}'
        }), 500

@tournaments_bp.route('/crawler/status', methods=['GET'])
@admin_required
def crawler_status():
    """Get status information about the crawler"""
    try:
        import os
        from datetime import datetime
        
        log_file = os.path.join(os.path.dirname(__file__), '..', 'logs', 'crawler.log')
        
        status = {
            'log_file_exists': os.path.exists(log_file),
            'last_run': None,
            'recent_logs': [],
            'crawler_configured': True
        }
        
        # Try to get last run time and recent logs from log file
        if os.path.exists(log_file):
            try:
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    # Get last 20 lines for recent logs
                    status['recent_logs'] = [line.strip() for line in lines[-20:] if line.strip()]
                    
                    # Try to extract last run time
                    for line in reversed(lines):
                        if 'Starting scheduled crawler run' in line or 'Crawler run completed' in line:
                            # Extract timestamp from log line
                            parts = line.split(' - ')
                            if len(parts) > 0:
                                timestamp_str = parts[0]
                                try:
                                    status['last_run'] = timestamp_str
                                    break
                                except:
                                    pass
            except Exception as e:
                status['log_error'] = str(e)
        
        # Check for existing tournaments from chess-results.com
        tournaments_count = Tournament.query.filter(
            Tournament.name.like('%Chess%') | 
            Tournament.name.like('%Schach%')
        ).count()
        status['imported_tournaments'] = tournaments_count
        
        return jsonify(status)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error getting crawler status: {str(e)}'
        }), 500

