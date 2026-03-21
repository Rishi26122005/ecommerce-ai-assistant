"""
Database models using Flask-SQLAlchemy
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"

    id            = db.Column(db.Integer, primary_key=True)
    name          = db.Column(db.String(120), nullable=False)
    email         = db.Column(db.String(200), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship
    history = db.relationship("ChatHistory", backref="user", lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.email}>"


class ChatHistory(db.Model):
    __tablename__ = "chat_history"

    id           = db.Column(db.Integer, primary_key=True)
    user_id      = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    query        = db.Column(db.Text, nullable=False)
    ai_response  = db.Column(db.Text, nullable=False)
    products_json = db.Column(db.Text, default="[]")   # JSON string of retrieved products
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<ChatHistory {self.id} user={self.user_id}>"


def init_db(app):
    """Create all tables if they don't exist."""
    with app.app_context():
        db.create_all()
        print("✅ Database initialized.")
