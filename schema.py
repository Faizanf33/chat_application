from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from enum import Enum
from datetime import datetime

db = SQLAlchemy()


class SenderType(Enum):
    """
    SenderType enum:
    - USER : 1
    - BOT : 2
    """

    USER = 1
    BOT = 2


class User(UserMixin, db.Model):
    """
    UserMixin provides default implementations for the methods that Flask-Login
    expects user objects to have.

    UserMixin provides the following properties and methods:
    - is_authenticated: a property that is True if the user has valid credentials
    - is_active: a property that is True if the user's account is active
    - is_anonymous: a property that is False for regular users
    - get_id(): a method that returns a unique identifier for the user as a string

    User model:
    - id: primary key
    - username: unique username
    - fullname: user's full name
    - email: unique email
    - password: hashed password
    """

    __tablename__ = "users"
    id = db.Column(db.Integer(), primary_key=True)
    username = db.Column(db.String(64), unique=True)
    fullname = db.Column(db.String(128), nullable=True)
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(128))
    created_at = db.Column(db.DateTime(), default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(), onupdate=datetime.utcnow)

    def __init__(self, username: str, email: str, password: str):
        self.username = username
        self.email = email
        self.set_password(password)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def get_json(self):
        return {"id": self.id, "username": self.username, "email": self.email}


class Bot(db.Model):
    """
    Bot model:
    - id: primary key
    - name: name of the bot
    - description: description of the bot
    """

    __tablename__ = "bots"
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(64))
    description = db.Column(db.Text())

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    def get_json(self):
        return {"id": self.id, "name": self.name, "description": self.description}


class Conversation(db.Model):
    """
    Conversation model:
    - id: primary key
    - user_id: foreign key to users table
    - bot_id: foreign key to bots table
    """

    __tablename__ = "conversations"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey("users.id"))
    bot_id = db.Column(db.Integer(), db.ForeignKey("bots.id"))
    timestamp = db.Column(db.DateTime(), default=datetime.utcnow)

    messages = db.relationship("Message", backref="conversations", lazy=True)

    def __init__(self, user_id: int, bot_id: int):
        self.user_id = user_id
        self.bot_id = bot_id

    def get_json(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "bot": Bot.query.get(self.bot_id).get_json(),
        }


class Message(db.Model):
    """
    Message model:
    - id: primary key
    - conversation_id: foreign key to conversations table
    - sender_id: foreign key to users or bots table
    - sender_type: sender type (user/bot)
    - receiver_id: foreign key to users or bots table
    - message: message content (text/imoji)
    - feedback: feedback (1-5)
    - timestamp: message timestamp
    """

    __tablename__ = "messages"
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer(), db.ForeignKey("conversations.id"))
    sender_id = db.Column(db.Integer())
    sender_type = db.Column(db.Enum(SenderType))
    receiver_id = db.Column(db.Integer())
    message = db.Column(db.Text())
    feedback = db.Column(db.Integer(), nullable=False, default=0)
    timestamp = db.Column(db.DateTime(), default=datetime.utcnow)

    def __init__(
        self,
        conversation_id: int,
        sender_id: int,
        receiver_id: int,
        message: str,
        sender_type: SenderType = SenderType.USER,
    ):
        self.conversation_id = conversation_id
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.message = message
        self.sender_type = sender_type

    def get_json(self):
        return {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "sender_type": self.sender_type.name,
            "message": self.message,
            "feedback": self.feedback,
            "timestamp": self.timestamp.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "date": self.timestamp.strftime("%d/%m/%Y"),
            "time": self.timestamp.strftime("%I:%M %p"),
        }
