import os

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user, login_required
from models import db, Admin
from werkzeug.security import generate_password_hash

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    admins = Admin.query.all()
    if not admins:
        new_admin = Admin(
            username = os.getenv('ADMIN_USERNAME'),
            password = os.getenv('ADMIN_PASSWORD'),
            email = os.getenv('ADMIN_EMAIL')
        )
        db.session.add(new_admin)
        db.session.commit()

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        admin = Admin.query.filter_by(username=username).first()

        if admin and admin.verify_password(password):
            login_user(admin)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('index'))
        flash('Invalid credentials', 'danger')

    return render_template('auth/login.html')
#
# @auth_bp.route('/signup', methods=['GET', 'POST'])
# def signup():
#     if request.method == 'POST':
#         username = request.form['username']
#         email = request.form['email']
#         password = generate_password_hash(request.form['password'], method='pbkdf2:sha256')
#
#         if Admin.query.filter_by(email=email).first():
#             flash('Email already exists!', 'danger')
#             return redirect(url_for('auth.signup'))
#
#         new_admin = Admin(username=username, email=email, password=password)
#         db.session.add(new_admin)
#         db.session.commit()
#
#         flash('Admin account created successfully!', 'success')
#         return redirect(url_for('auth.login'))
#
#     return render_template('auth/signup.html')

@auth_bp.route('/logout', methods=['GET'])
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!', 'info')
    return redirect(url_for('auth.login'))
