from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash
from uuid import uuid4
from models import db, Group, User
from werkzeug.security import generate_password_hash

groups_bp = Blueprint('groups', __name__, url_prefix='/groups')

# Add a new group
@groups_bp.route('/add', methods=['GET', 'POST'])
def add_group():
    if request.method == 'POST':
        name = request.form['name']

        # Validate input
        if not name:
            flash('Group name is required!', 'danger')
            return redirect(url_for('groups.add_group'))

        if Group.query.filter_by(name=name).first():
            flash('Group already exists!', 'danger')
            return redirect(url_for('groups.add_group'))

        new_group = Group(id=uuid4().hex, name=name)
        db.session.add(new_group)
        db.session.commit()

        flash('Group added successfully!', 'success')
        return redirect(url_for('groups.list_groups'))
    return render_template('groups/add_group.html')

# List all groups
@groups_bp.route('/', methods=['GET'])
def list_groups():
    groups = Group.query.all()
    return render_template('groups/index.html', groups=groups)

# View users in a group
@groups_bp.route('/<group_id>/users', methods=['GET'])
def group_users(group_id):
    group = Group.query.get_or_404(group_id)
    return render_template('groups/group_users.html', group=group)


@groups_bp.route('/group/<group_id>/add_user', methods=['GET', 'POST'])
def add_user_to_group(group_id):
    group = Group.query.get_or_404(group_id)
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        days = int(request.form['active_days'])
        hours = int(request.form['active_hours'])
        
        # Calculate the disabled_after datetime
        disabled_after = datetime.utcnow() + timedelta(days=days, hours=hours)

        # Create new user with the provided details
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(
            username=username,
            email=email,
            password=hashed_password,
            disabled_after=disabled_after
        )

        # Check if the user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('User with this email already exists', 'danger')
            return redirect(url_for('groups.add_user_to_group', group_id=group.id))
        
        existing_username = User.query.filter_by(username=username).first()
        if existing_username:
            flash('User with this username already exists', 'danger')
            return redirect(url_for('groups.add_user_to_group', group_id=group.id))

        # Add user to the group
        new_user.group = group
        db.session.add(new_user)
        db.session.commit()

        flash('User added to the group successfully!', 'success')
        return redirect(url_for('groups.group_users', group_id=group.id))

    # Fetch users who are not part of any group (unassigned)
    users = User.query.filter(User.group == None).all()
    return render_template('groups/add_user_to_group.html', group=group, users=users)



