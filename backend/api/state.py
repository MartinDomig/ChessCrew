from flask import Blueprint, jsonify
from ..db.models import User

state_bp = Blueprint('state', __name__)

@state_bp.route('/state', methods=['GET'])
def get_state():
    # Check if any admin user exists
    admin_exists = User.query.filter_by(is_admin=True).first() is not None
    return jsonify({
        'needs_admin': not admin_exists
    })
