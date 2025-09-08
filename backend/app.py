import os
from flask import Flask, render_template
from api.endpoints import register_blueprints
from db.models import db
from sqlalchemy import text, inspect, Boolean, Integer, String, Date, Float, Text
from db.models import Player, Tournament, TournamentPlayer, Game, User, Note, Tag

def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get('FLASK_SECRET_KEY')
    if not app.secret_key:
        raise RuntimeError('FLASK_SECRET_KEY environment variable must be set.')
    
    # Set session configuration for better persistence
    app.config['PERMANENT_SESSION_LIFETIME'] = 90 * 24 * 60 * 60  # 90 days
    app.config['SESSION_REFRESH_EACH_REQUEST'] = True  # Refresh session on each request
    app.config['SESSION_PERMANENT'] = True  # Make sessions permanent by default
    
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
    
    # Database connection pool configuration
    app.config['SQLALCHEMY_POOL_SIZE'] = 10
    app.config['SQLALCHEMY_POOL_TIMEOUT'] = 30
    app.config['SQLALCHEMY_POOL_RECYCLE'] = 3600
    app.config['SQLALCHEMY_MAX_OVERFLOW'] = 20
    
    # Set session cookie for cross-origin credentials
    app.config['SESSION_COOKIE_SAMESITE'] = 'None'
    app.config['SESSION_COOKIE_SECURE'] = True

    db.init_app(app)
    with app.app_context():
        db.create_all()
        # Add missing columns to existing tables
        add_missing_columns()

    # Register API routes
    register_blueprints(app)

    # Index page route
    @app.route('/')
    def index():
        return render_template('index.html')

    return app

def add_missing_columns():
    """Automatically add missing columns to existing database tables by comparing model definitions with database schema."""
    inspector = inspect(db.engine)
    
    # Define all models to check
    models_to_check = [Player, Tournament, TournamentPlayer, Game, User, Note, Tag]
    
    for model in models_to_check:
        table_name = model.__tablename__
        
        if table_name not in inspector.get_table_names():
            print(f"Table '{table_name}' does not exist, skipping...")
            continue
            
        print(f"Checking table '{table_name}' for missing columns...")
        existing_columns = {col['name']: col for col in inspector.get_columns(table_name)}
        
        # Check each column in the model
        for column in model.__table__.columns:
            column_name = column.name
            
            if column_name not in existing_columns:
                print(f"  Adding missing column '{column_name}' to table '{table_name}'...")
                
                # Generate SQL for the column based on its type
                sql_type = get_sql_type_for_column(column)
                nullable = "NULL" if column.nullable else "NOT NULL"
                default = get_default_value_sql(column)
                
                alter_sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {sql_type} {nullable} {default}"
                
                try:
                    with db.engine.connect() as conn:
                        conn.execute(text(alter_sql))
                        conn.commit()
                    print(f"    ✓ Column '{column_name}' added successfully!")
                except Exception as e:
                    print(f"    ✗ Failed to add column '{column_name}': {e}")

def get_sql_type_for_column(column):
    """Convert SQLAlchemy column type to SQL type string."""
    column_type = column.type
    
    if isinstance(column_type, Boolean):
        return "BOOLEAN"
    elif isinstance(column_type, Integer):
        return "INTEGER"
    elif isinstance(column_type, String):
        return f"VARCHAR({column_type.length or 80})"
    elif isinstance(column_type, Date):
        return "DATE"
    elif isinstance(column_type, Float):
        return "FLOAT"
    elif isinstance(column_type, Text):
        return "TEXT"
    else:
        # Fallback for unknown types
        return str(column_type).upper()

def get_default_value_sql(column):
    """Generate SQL default value clause for a column."""
    if column.default is not None:
        if hasattr(column.default, 'arg'):
            # SQLAlchemy DefaultClause
            default_value = column.default.arg
            if isinstance(default_value, bool):
                return f"DEFAULT {int(default_value)}"
            elif isinstance(default_value, (int, float)):
                return f"DEFAULT {default_value}"
            elif isinstance(default_value, str):
                return f"DEFAULT '{default_value}'"
        elif callable(column.default):
            # For callable defaults like datetime.now
            return ""
    
    # For server defaults or no default
    if column.server_default is not None:
        return f"DEFAULT {column.server_default.arg}"
    
    return ""

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

