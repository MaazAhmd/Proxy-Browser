from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, User
from werkzeug.security import generate_password_hash, check_password_hash

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid credentials', 'danger')

    return render_template('auth/login.html')

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'], method='sha256')

        user = User(username=username, email=email, password=password)
        db.session.add(user)
        db.session.commit()

        flash('Signup successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/signup.html')
