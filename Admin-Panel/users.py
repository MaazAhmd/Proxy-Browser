from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, User
from werkzeug.security import generate_password_hash

users_bp = Blueprint('users', __name__, url_prefix='/users')

# View all users
@users_bp.route('/')
def index():
    search_query = request.args.get('search', '')
    if search_query:
        users = User.query.filter(User.username.ilike(f'%{search_query}%')).all()
    else:
        users = User.query.all()
    return render_template('users/index.html', users=users, search_query=search_query)

# Add a new user
@users_bp.route('/add', methods=['GET', 'POST'])
def add_user():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # Validate input
        if not username or not email or not password:
            flash('Username, Email, and Password are required!', 'danger')
            return redirect(url_for('users.add_user'))

        # Hash the password
        hashed_password = generate_password_hash(request.form['password'], method='pbkdf2:sha256')


        new_user = User(username=username, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash('User added successfully!', 'success')
        return redirect(url_for('users.index'))
    return render_template('users/add_user.html')

# Edit user details
@users_bp.route('/edit/<string:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        user.username = request.form['username']
        user.email = request.form['email']

        # Handle password update
        new_password = request.form.get('password')
        if new_password:
            user.password = generate_password_hash(new_password, method='sha256')

        db.session.commit()

        flash('User updated successfully!', 'success')
        return redirect(url_for('users.index'))
    return render_template('users/edit_user.html', user=user)

# Delete a user
@users_bp.route('/delete/<string:user_id>', methods=['POST'])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()

    flash('User deleted successfully!', 'success')
    return redirect(url_for('users.index'))
