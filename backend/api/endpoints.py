from functools import wraps
import json
import os
import tempfile
import subprocess
from flask import Flask, Blueprint, jsonify, request, current_app, session, abort, Response
from db.models import db, Player, User, Tag, Note
from .state import state_bp
from .players import players_bp
from .tournaments import tournaments_bp
from .auth import login_required, admin_required

api = Blueprint('api', __name__)

# Register state endpoint blueprint
def register_blueprints(app):
    app.register_blueprint(state_bp, url_prefix='/api')
    app.register_blueprint(api, url_prefix='/api')
    app.register_blueprint(players_bp, url_prefix='/api')
    app.register_blueprint(tournaments_bp, url_prefix='/api')


######
# Implement endpoints below
######

# List users
@api.route('/users', methods=['GET'])
@admin_required
def list_users():
    users = User.query.all()
    return jsonify([
        {'id': u.id, 'username': u.username, 'admin': u.admin}
        for u in users
    ])

# Add user
@api.route('/users', methods=['POST'])
@admin_required
def add_user():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    admin = bool(data.get('admin'))
    if not username or not password:
        return jsonify({'error': 'Benutzername und Passwort erforderlich.'}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Benutzer existiert bereits.'}), 409
    user = User(username=username, admin=admin)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return jsonify({'status': 'created'}), 201

# Update user
@api.route('/users/<int:user_id>', methods=['PUT'])
@admin_required
def update_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'Benutzer nicht gefunden.'}), 404
    data = request.get_json()
    username = data.get('username')
    admin = bool(data.get('admin'))
    password = data.get('password')
    # Check for username conflict
    if username and username != user.username:
        if User.query.filter_by(username=username).first():
            return jsonify({'error': 'Benutzername existiert bereits.'}), 409
        user.username = username
    user.admin = admin
    if password:
        user.set_password(password)
    db.session.commit()
    return jsonify({'status': 'updated'})

# Delete user
@api.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'Benutzer nicht gefunden.'}), 404
    db.session.delete(user)
    db.session.commit()
    return jsonify({'status': 'deleted'})

# Change password
@api.route('/users/<int:user_id>/password', methods=['POST'])
@admin_required
def change_password(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'Benutzer nicht gefunden.'}), 404
    data = request.get_json()
    password = data.get('password')
    if not password:
        return jsonify({'error': 'Passwort erforderlich.'}), 400
    user.set_password(password)
    db.session.commit()
    return jsonify({'status': 'password changed'})

# Endpoint to create first admin user if no users exist
@api.route('/setup-admin', methods=['POST'])
def setup_admin():
    if User.query.first():
        return jsonify({'error': 'Admin existiert bereits.'}), 409
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'error': 'Benutzername und Passwort erforderlich.'}), 400
    user = User(username=username, is_admin=True)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return jsonify({'status': 'admin created'}), 201

# Login endpoint
@api.route('/login', methods=['POST'])
def login():
    # If no users exist, signal frontend to redirect to admin setup
    if not User.query.first():
        return jsonify({'setup_admin': True}), 403
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        session['user_id'] = user.id
        return jsonify({'status': 'ok'}), 200
    return jsonify({'error': 'Invalid credentials'}), 401

# Logout endpoint
@api.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return jsonify({'status': 'logged out'}), 200

# Check login status
@api.route('/session/user', methods=['GET'])
def get_logged_in_user():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'logged_in': False}), 200
    user = User.query.get(user_id)
    if not user:
        return jsonify({'logged_in': False}), 200
    return jsonify({'logged_in': True, 'username': user.username, 'admin': user.is_admin}), 200

@api.route('/session/set', methods=['POST'])
def set_session():
    data = request.get_json()
    month = data.get('month')
    year = data.get('year')
    emp = data.get('employee_id')
    if month:
        session['month'] = month
    if year:
        session['year'] = year
    if emp:
        session['employee_id'] = emp
    elif emp is not None:
        session.pop('employee_id', None)
    return jsonify({'status': 'ok', 'month': session.get('month'), 'year': session.get('year'), 'employee_id': session.get('employee_id')}), 200

@api.route('/session/get', methods=['GET'])
def get_session():
    return jsonify({
        'month': session.get('month'),
        'year': session.get('year'),
        'employee_id': session.get('employee_id')
    }), 200

@api.route('/tags', methods=['GET'])
@login_required
def list_tags():
    tags = Tag.query.all()
    return jsonify([{'id': t.id, 'name': t.name, 'color': t.color} for t in tags])

@api.route('/tags', methods=['POST'])
@login_required
def create_tag():
    data = request.get_json()
    name = data.get('name')
    color = data.get('color')
    if not name:
        return jsonify({'error': 'Tag-Name erforderlich.'}), 400
    if Tag.query.filter_by(name=name).first():
        return jsonify({'error': 'Tag existiert bereits.'}), 409
    tag = Tag(name=name, color=color)
    db.session.add(tag)
    db.session.commit()
    return jsonify({'id': tag.id, 'name': tag.name, 'color': tag.color}), 201

@api.route('/tags/<int:tag_id>', methods=['DELETE'])
@admin_required
def delete_tag(tag_id):
    tag = Tag.query.get(tag_id)
    if not tag:
        return jsonify({'error': 'Tag nicht gefunden.'}), 404
    
    # Check if tag is still assigned to players
    if tag.players:
        return jsonify({'error': 'Tag ist noch Spielern zugewiesen und kann nicht gelöscht werden.'}), 409
    
    db.session.delete(tag)
    db.session.commit()
    return jsonify({'status': 'deleted'})

@api.route('/players/<int:player_id>/tags', methods=['POST'])
@login_required
def add_tag_to_player(player_id):
    player = Player.query.get(player_id)
    if not player:
        return jsonify({'error': 'Spieler nicht gefunden.'}), 404
    data = request.get_json()
    tag_id = data.get('tag_id')
    tag = Tag.query.get(tag_id)
    if not tag:
        return jsonify({'error': 'Tag nicht gefunden.'}), 404
    if tag in player.tags:
        return jsonify({'error': 'Tag bereits zugewiesen.'}), 409
    player.tags.append(tag)
    db.session.commit()
    return jsonify({'status': 'added'})

@api.route('/players/<int:player_id>/tags/<int:tag_id>', methods=['DELETE'])
@login_required
def remove_tag_from_player(player_id, tag_id):
    player = Player.query.get(player_id)
    if not player:
        return jsonify({'error': 'Spieler nicht gefunden.'}), 404
    tag = Tag.query.get(tag_id)
    if not tag:
        return jsonify({'error': 'Tag nicht gefunden.'}), 404
    if tag not in player.tags:
        return jsonify({'error': 'Tag nicht zugewiesen.'}), 409
    player.tags.remove(tag)
    db.session.commit()
    return jsonify({'status': 'removed'})

@api.route('/players/<int:player_id>/tags', methods=['GET'])
@login_required
def get_player_tags(player_id):
    player = Player.query.get(player_id)
    if not player:
        return jsonify({'error': 'Spieler nicht gefunden.'}), 404
    return jsonify([{'id': t.id, 'name': t.name, 'color': t.color} for t in player.tags])

@api.route('/email/tags', methods=['GET'])
@login_required
def get_email_tags():
    """Get all tags with player counts for email purposes"""
    tags = Tag.query.all()
    result = []

    for tag in tags:
        player_count = len([p for p in tag.players if p.email and p.email.strip()])
        result.append({
            'id': tag.id,
            'name': tag.name,
            'color': tag.color,
            'player_count': player_count,
            'email_address': f'chesscrew.{tag.name}@domig.net'
        })

    return jsonify(result)

@api.route('/email/preview/<int:tag_id>', methods=['POST'])
@login_required
def preview_email(tag_id):
    """Preview how an email would look for players with a specific tag"""
    tag = Tag.query.get(tag_id)
    if not tag:
        return jsonify({'error': 'Tag nicht gefunden.'}), 404

    data = request.get_json()
    subject = data.get('subject', '')
    body = data.get('body', '')

    # Get first player with email for preview
    preview_player = None
    for player in tag.players:
        if player.email and player.email.strip():
            preview_player = player
            break

    if not preview_player:
        return jsonify({'error': 'Keine Spieler mit E-Mail-Adresse in dieser Gruppe gefunden.'}), 404

    # Apply personalization
    greeting = "Liebe" if preview_player.female else "Lieber"
    personalized_subject = subject.replace('{firstname}', preview_player.first_name)
    personalized_subject = personalized_subject.replace('{lastname}', preview_player.last_name)
    personalized_subject = personalized_subject.replace('{name}', preview_player.name)
    personalized_subject = personalized_subject.replace('{greeting}', greeting)

    personalized_body = body.replace('{firstname}', preview_player.first_name)
    personalized_body = personalized_body.replace('{lastname}', preview_player.last_name)
    personalized_body = personalized_body.replace('{name}', preview_player.name)
    personalized_body = personalized_body.replace('{greeting}', greeting)
    personalized_body = personalized_body.replace('{email}', preview_player.email)

    return jsonify({
        'preview_player': {
            'name': preview_player.name,
            'email': preview_player.email,
            'gender': 'female' if preview_player.female else 'male'
        },
        'personalized_subject': personalized_subject,
        'personalized_body': personalized_body,
        'total_recipients': len([p for p in tag.players if p.email and p.email.strip()])
    })

@api.route('/email/send-test/<int:tag_id>', methods=['POST'])
@login_required
def send_test_email(tag_id):
    """Send a test email to the first player in a tag group"""
    tag = Tag.query.get(tag_id)
    if not tag:
        return jsonify({'error': 'Tag nicht gefunden.'}), 404

    data = request.get_json()
    subject = data.get('subject', '')
    body = data.get('body', '')

    # Find first player with email
    test_player = None
    for player in tag.players:
        if player.email and player.email.strip():
            test_player = player
            break

    if not test_player:
        return jsonify({'error': 'Keine Spieler mit E-Mail-Adresse in dieser Gruppe gefunden.'}), 404

    # Here you would integrate with your email sending system
    # For now, just return success
    return jsonify({
        'status': 'Test-E-Mail würde an {} gesendet werden'.format(test_player.email),
        'recipient': {
            'name': test_player.name,
            'email': test_player.email
        }
    })

@api.route('/email/stats', methods=['GET'])
@login_required
def get_email_stats():
    """Get email statistics for all tags"""
    tags = Tag.query.all()
    total_players = Player.query.count()
    players_with_email = Player.query.filter(Player.email.isnot(None), Player.email != '').count()

    tag_stats = []
    for tag in tags:
        players_in_tag = len(tag.players)
        players_with_email_in_tag = len([p for p in tag.players if p.email and p.email.strip()])

        tag_stats.append({
            'tag_name': tag.name,
            'total_players': players_in_tag,
            'players_with_email': players_with_email_in_tag,
            'email_percentage': round((players_with_email_in_tag / players_in_tag * 100), 1) if players_in_tag > 0 else 0
        })

    return jsonify({
        'overall': {
            'total_players': total_players,
            'players_with_email': players_with_email,
            'email_percentage': round((players_with_email / total_players * 100), 1) if total_players > 0 else 0
        },
        'tags': tag_stats
    })

def register_routes(app):
    app.register_blueprint(api, url_prefix='/api')
