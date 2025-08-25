from flask import Blueprint, request, jsonify, abort, session
from backend.db.models import db, Player
from .auth import login_required, admin_required

players_bp = Blueprint('players', __name__)

@players_bp.route('/players', methods=['GET'])
@login_required
def list_players():
    players = Player.query.all()
    return jsonify([
        {'id': p.id, 'username': p.username, 'rating': getattr(p, 'rating', None)}
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

@players_bp.route('/players/<int:player_id>', methods=['PUT'])
@login_required
def update_player(player_id):
    player = Player.query.get(player_id)
    if not player:
        return jsonify({'error': 'Player not found'}), 404
    data = request.get_json()
    username = data.get('username')
    rating = data.get('rating')
    if username:
        player.username = username
    if rating is not None:
        player.rating = rating
    db.session.commit()
    return jsonify({'id': player.id, 'username': player.username, 'rating': player.rating})

@players_bp.route('/players/<int:player_id>', methods=['DELETE'])
@login_required
def delete_player(player_id):
    player = Player.query.get(player_id)
    if not player:
        return jsonify({'error': 'Player not found'}), 404
    db.session.delete(player)
    db.session.commit()
    return jsonify({'status': 'deleted'})
