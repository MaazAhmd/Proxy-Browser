import datetime
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
    id = db.Column(db.String(32), primary_key=True, default=lambda: uuid4().hex)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    disabled_after = db.Column(db.DateTime, nullable=True)
    disabled = db.Column(db.Boolean, nullable=False, default=False)
    
    proxy_id = db.Column(db.String(64), db.ForeignKey('proxy.id'), nullable=True)
    proxy = db.relationship('Proxy', back_populates='assigned_to_users')  # Relationship with Proxy
    
    group_id = db.Column(db.String(32), db.ForeignKey('group.id'), nullable=True) 
    group = db.relationship('Group', back_populates='users')  # Relationship with Group
    
    def set_disabled_after(self, days, hours):
        """Set the disabled_after time based on days and hours"""
        self.disabled_after = datetime.utcnow() + datetime.timedelta(days=days, hours=hours)
        db.session.commit()

    def get_proxy_hostname(self):
        proxy = Proxy.query.filter_by(id=self.proxy_id).first()
        if proxy:
            return proxy.host
        return None

    def __repr__(self):
        return self.username
    

class Proxy(db.Model):
    id = db.Column(db.String(32), primary_key=True, default=lambda: uuid4().hex)  # 32-character UUID
    username = db.Column(db.String(256), nullable=False)
    password = db.Column(db.Text, nullable=False)
    host = db.Column(db.String(256), nullable=False)
    port = db.Column(db.String(16), nullable=False)
    
    assigned_to_users = db.relationship('User', back_populates='proxy', cascade="all, delete-orphan")
    
    
class Group(db.Model):
    id = db.Column(db.String(32), primary_key=True, default=lambda: uuid4().hex)
    name = db.Column(db.String(100), unique=True, nullable=False)

    users = db.relationship('User', back_populates='group', cascade="all, delete-orphan")

