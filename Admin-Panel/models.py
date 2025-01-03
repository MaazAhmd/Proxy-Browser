from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from uuid import uuid4
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class Admin(UserMixin, db.Model):
    id = db.Column(db.String(64), primary_key=True)
    username = db.Column(db.String(256), unique=True, nullable=False)
    email = db.Column(db.String(256), unique=True, nullable=False)
    password = db.Column(db.Text, nullable=False)
    
    def verify_password(self, password):
        return check_password_hash(self.password, password)


class User(db.Model):
    id = db.Column(db.String(64), primary_key=True)
    username = db.Column(db.String(256), unique=True, nullable=False)
    email = db.Column(db.String(256), unique=True, nullable=False)
    password = db.Column(db.Text, nullable=False)
    proxies = db.relationship('Proxy', backref='user', lazy=True)
    

class Proxy(db.Model):
    id = db.Column(db.String(64), primary_key=True)
    username = db.Column(db.String(256), unique=True, nullable=False)
    password = db.Column(db.Text, nullable=False)
    host = db.Column(db.String(256), unique=True, nullable=False)
    port = db.Column(db.String(16), unique=True, nullable=False)
    assigned_to = db.Column(db.String(64), db.ForeignKey('user.id'), nullable=True)
