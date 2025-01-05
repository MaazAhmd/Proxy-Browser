from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from uuid import uuid4
from models import db, Proxy, User
from werkzeug.security import check_password_hash

proxies_bp = Blueprint('proxy', __name__, url_prefix='/proxies')

# Add a new proxy
@proxies_bp.route('/add', methods=['GET', 'POST'])
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
    return render_template('proxies/add_proxy.html')

# List all proxies
@proxies_bp.route('/', methods=['GET'])
def index():
    proxies = Proxy.query.all()
    return render_template('proxies/index.html', proxies=proxies)

# Assign proxy to a user
@proxies_bp.route('/assign', methods=['GET', 'POST'])
def assign_proxy():
    users = User.query.all()
    proxies = Proxy.query.filter_by(assigned_to=None).all()

    if request.method == 'POST':
        proxy_id = request.form['proxy_id']
        user_id = request.form['user_id']

        # Validate input
        if not proxy_id or not user_id:
            flash('Both proxy and user must be selected!', 'danger')
            return redirect(url_for('proxy.assign_proxy'))

        # Assign the proxy
        proxy = Proxy.query.get(proxy_id)
        if not proxy:
            flash('Invalid proxy selected!', 'danger')
            return redirect(url_for('proxy.assign_proxy'))

        proxy.assigned_to = user_id
        db.session.commit()

        flash('Proxy assigned successfully!', 'success')
        return redirect(url_for('proxy.index'))

    return render_template('proxies/assign_proxy.html', users=users, proxies=proxies)


@proxies_bp.route('/get-proxy', methods=['POST'])
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

    proxy = Proxy.query.filter_by(assigned_to=user.id).first()
    if not proxy:
        return jsonify({'status': 0, 'error_message': 'No proxy assigned to this user'}), 200

    proxy_details = {
        'proxy_url': proxy.host,
        'proxy_port': proxy.port,
        'proxy_user': proxy.username,
        'proxy_password': proxy.password
    }

    return jsonify({'status': 1, 'proxy_details': proxy_details, 'message': 'Login successful'}), 200