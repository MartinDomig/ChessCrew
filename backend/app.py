import os
from flask import Flask, render_template
from backend.api.endpoints import register_blueprints
from backend.db.models import db

def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get('FLASK_SECRET_KEY')
    if not app.secret_key:
        raise RuntimeError('FLASK_SECRET_KEY environment variable must be set.')
    
    # Set Flask environment (automatically sets DEBUG based on FLASK_ENV)
    flask_env = os.environ.get('FLASK_ENV', 'production')
    app.config['ENV'] = flask_env
    if flask_env == 'development':
        app.config['DEBUG'] = True
    else:
        app.config['DEBUG'] = False
    
    # Set up configurations
    db_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'db')
    os.makedirs(db_dir, exist_ok=True)
    db_path = os.path.join(db_dir, 'chesscrew.sqlite3')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    # Set session cookie for cross-origin credentials
    app.config['SESSION_COOKIE_SAMESITE'] = 'None'
    app.config['SESSION_COOKIE_SECURE'] = True

    db.init_app(app)
    with app.app_context():
        db.create_all()

    # Register API routes
    register_blueprints(app)

    # Index page route
    @app.route('/')
    def index():
        return render_template('index.html')

    return app

if __name__ == '__main__':
    app = create_app()
    
    # Security check: Warn if debug mode is enabled
    if app.config.get('DEBUG', False):
        flask_env = os.environ.get('FLASK_ENV', 'production')
        if flask_env == 'production':
            print("⚠️  WARNING: Debug mode is enabled in production environment!")
            print("   This is a security risk and should be disabled.")
            print("   Set FLASK_ENV=production or remove DEBUG from environment.")
            print("   For production, use a WSGI server like gunicorn instead of app.run()")
        else:
            print("🔧 Debug mode enabled (development environment)")
    
    app.run(port=15001)

