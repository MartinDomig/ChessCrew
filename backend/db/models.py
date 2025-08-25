from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

# The db object should be created in your Flask app and imported here
db = SQLAlchemy()

class Player(db.Model):
    __tablename__ = 'players'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    p_number = db.Column(db.Integer, unique=True, nullable=False)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    elo = db.Column(db.Integer, nullable=False)
    fide_number = db.Column(db.Integer, nullable=True)
    fide_elo = db.Column(db.Integer, nullable=True)
    birthday = db.Column(db.Date, nullable=True)
    kat = db.Column(db.String(10), nullable=True)
    zip = db.Column(db.String(10), nullable=True)
    town = db.Column(db.String(80), nullable=True)
    country = db.Column(db.String(3), nullable=True)
    phone = db.Column(db.String(15), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    club = db.Column(db.String(80), nullable=True)
    is_active = db.Column(db.Boolean, default=False)
    female = db.Column(db.Boolean, default=False)
    tags = db.relationship('Tag', secondary='player_tags', back_populates='players')
    notes = db.relationship('Note', back_populates='player')

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Tag(db.Model):
    __tablename__ = 'tags'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(200), nullable=True)
    color = db.Column(db.String(7), nullable=True)  # Store color as hex string
    players = db.relationship('Player', secondary='player_tags', back_populates='tags')

class Note(db.Model):
    __tablename__ = 'notes'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    player_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    manual = db.Column(db.Boolean, default=False)

    player = db.relationship('Player', back_populates='notes')

# Association table for many-to-many relationship between Player and Tag
player_tags = db.Table('player_tags',
    db.Column('player_id', db.Integer, db.ForeignKey('players.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id'), primary_key=True)
)
