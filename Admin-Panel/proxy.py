from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from uuid import uuid4

from flask_login import login_required

from models import db, Proxy, User
import jwt
import os
from functools import wraps
from models import db, Proxy, User, Group
from werkzeug.security import check_password_hash

proxies_bp = Blueprint('proxy', __name__, url_prefix='/proxies')


# List all proxies
@proxies_bp.route('/', methods=['GET'])
@login_required
def index():
    proxies = Proxy.query.all()
    for proxy in proxies:
        print(proxy.assigned_to_users)

    return render_template('proxies/index.html', proxies=proxies, page='proxies')


# Add a new proxy
@proxies_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_proxy():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        host = request.form['host']
        port = request.form['port']

        # Validate input
        if not username or not password or not host or not port:
            flash('All fields are required!', 'danger')
            return redirect(url_for('proxy.add_proxy'))

        # Check for unique constraints
        if Proxy.query.filter((Proxy.username == username) | (Proxy.host == host) | (Proxy.port == port)).first():
            flash('Proxy details must be unique!', 'danger')
            return redirect(url_for('proxy.add_proxy'))

        # Create a new proxy
        new_proxy = Proxy(
            id=uuid4().hex,
            username=username,
            password=password,
            host=host,
            port=port,
        )
        db.session.add(new_proxy)
        db.session.commit()

        flash('Proxy added successfully!', 'success')
        return redirect(url_for('proxy.index'))
    return render_template('proxies/add_proxy.html', page='proxies')

@proxies_bp.route('/edit/<proxy_id>', methods=['GET', 'POST'])
@login_required
def edit_proxy(proxy_id):
    proxy = Proxy.query.get_or_404(proxy_id)

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        host = request.form.get('host')
        port = request.form.get('port')

        # Validate input
        if not username or not password or not host or not port:
            flash('All fields are required!', 'danger')
            return redirect(url_for('proxies.edit_proxy', proxy_id=proxy_id))

        # Check for unique constraints (excluding the current proxy being edited)
        existing_proxy = Proxy.query.filter(
            ((Proxy.username == username) |
             (Proxy.host == host) |
             (Proxy.port == port)) &
            (Proxy.id != proxy_id)
        ).first()

        if existing_proxy:
            flash('Proxy details must be unique!', 'danger')
            return redirect(url_for('proxies.edit_proxy', proxy_id=proxy_id))

        # Update proxy details
        proxy.username = username
        proxy.password = password
        proxy.host = host
        proxy.port = port

        db.session.commit()

        flash('Proxy updated successfully!', 'success')
        return redirect(url_for('proxies.index'))

    return render_template('proxies/edit_proxy.html', proxy=proxy, page='proxies')


@proxies_bp.route('/delete/<proxy_id>', methods=['POST'])
@login_required
def delete_proxy(proxy_id):
    proxy = Proxy.query.get_or_404(proxy_id)

    try:
        db.session.delete(proxy)
        db.session.commit()
        flash('Proxy deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting proxy: {e}', 'danger')

    return redirect(url_for('proxies.index'))


@proxies_bp.route('/assign', methods=['GET', 'POST'])
@login_required
def assign_proxy():
    if request.method == 'POST':
        data = request.get_json()
        proxy_id = data.get('proxy_id')
        user_ids = data.get('user_ids', [])

        if not proxy_id or not user_ids:
            return jsonify(success=False, message="Invalid input")

        proxy = Proxy.query.get(proxy_id)
        if not proxy:
            return jsonify(success=False, message="Proxy not found")

        users = User.query.filter(User.id.in_(user_ids)).all()
        for user in users:
            user.proxy_id = proxy_id

        db.session.commit()
        return jsonify(success=True)

    users = User.query.all()
    proxies = Proxy.query.all()
    return render_template(
        'proxies/assign_proxy.html', users=users, proxies=proxies, page='assign_proxies'
    )


@proxies_bp.route('/assign-to-group', methods=['GET', 'POST'])
@login_required
def assign_proxy_group():
    if request.method == 'POST':
        data = request.get_json()
        proxy_id = data.get('proxy_id')
        group_id = data.get('group_id')

        if not proxy_id or not group_id:
            return jsonify(success=False, message="Invalid input")

        group = Group.query.get(group_id)
        if not group:
            return jsonify(success=False, message="Group not found")

        proxy = Proxy.query.get(proxy_id)
        if not proxy:
            return jsonify(success=False, message="Proxy not found")

        # Overwrite any existing assignment
        for user in group.users:
            user.proxy_id = proxy_id

        db.session.commit()
        return jsonify(success=True)

    groups = Group.query.all()
    proxies = Proxy.query.all()
    return render_template(
        'proxies/assign_proxy_group.html', groups=groups, proxies=proxies, page='assign_proxies_group'
    )



def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']
        if not token:
            return jsonify({'status': 0, 'error_message': 'Token is missing!'}), 401
        try:
            data = jwt.decode(token, os.getenv('TOKEN_SECRET_KEY'), algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return jsonify({'status': 0, 'error_message': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'status': 0, 'error_message': 'Invalid token!'}), 401
        return f(*args, **kwargs)
    return decorated


@proxies_bp.route('/get-proxy', methods=['POST'])
@token_required
def get_proxy():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'status': 0, 'error_message': 'Username and password are required'}), 200

    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'status': 0, 'error_message': 'Username not found'}), 200

    if not check_password_hash(user.password, password):
        return jsonify({'status': 0, 'error_message': 'Incorrect password'}), 200

    if user.disabled:
        return jsonify({'status': 0, 'error_message': 'User Expired'}), 200

    if user.disabled_after <= datetime.now():
        user.disabled = True
        db.session.commit()
        return jsonify({'status': 0, 'error_message': 'User Expired'}), 200

    if not user.proxy_id :
        return jsonify({'status': 0, 'error_message': 'No proxy assigned to this user'}), 200

    proxy = Proxy.query.get(user.proxy_id)
    if not proxy:
        return jsonify({'status': 0, 'error_message': 'No proxy assigned to this user'}), 200

    proxy_details = {
        'proxy_url': proxy.host,
        'proxy_port': proxy.port,
        'proxy_user': proxy.username,
        'proxy_password': proxy.password
    }

    return jsonify({'status': 1, 'proxy_details': proxy_details, 'message': 'Login successful'}), 200