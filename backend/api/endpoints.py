from functools import wraps
import json
import os
import tempfile
import subprocess
from flask import Flask, Blueprint, jsonify, request, current_app, session, abort, Response
from db.models import db, Player, User, Tag, Note

api = Blueprint('api', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        user = User.query.get(user_id) if user_id else None
        if not user or not user.admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

# Helper decorator for login protection
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

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
    user = User(username=username, admin=True)
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
    return jsonify({'logged_in': True, 'username': user.username, 'admin': user.admin}), 200

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

def register_routes(app):
    app.register_blueprint(api, url_prefix='/api')
