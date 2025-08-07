from flask import Blueprint, render_template, request, send_file, redirect, url_for, flash
from models import db, User, Proxy
import csv
import io
from sqlalchemy.exc import IntegrityError

import_export_bp = Blueprint('import_export', __name__, url_prefix='/import_export')

@import_export_bp.route('/import-export')
def import_export_page():
    return render_template('import_export.html', title="Import/Export")

# ---------- EXPORT ----------
@import_export_bp.route('/export-users')
def export_users():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['username', 'email', 'password', 'session_limit'])
    for user in User.query.all():
        writer.writerow([user.username, user.email, user.password, user.session_limit])
    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode()), mimetype='text/csv',
                     download_name='users.csv', as_attachment=True)

@import_export_bp.route('/export-proxies')
def export_proxies():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['username', 'password', 'host', 'port'])
    for proxy in Proxy.query.all():
        writer.writerow([proxy.username, proxy.password, proxy.host, proxy.port])
    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode()), mimetype='text/csv',
                     download_name='proxies.csv', as_attachment=True)

# ---------- IMPORT ----------
@import_export_bp.route('/import-users', methods=['POST'])
def import_users():
    file = request.files.get('file')
    if not file:
        flash("No file uploaded", "danger")
        return redirect(url_for('import_export.import_export_page'))

    try:
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        reader = csv.DictReader(stream)
        count = 0
        for row in reader:
            user = User(
                username=row['username'].strip(),
                email=row['email'].strip(),
                password=row['password'].strip(),
                session_limit=int(row.get('session_limit', 1)),
            )
            db.session.add(user)
            count += 1
        db.session.commit()
        flash(f"{count} users imported successfully.", "success")
    except IntegrityError as e:
        db.session.rollback()
        flash(f"Integrity error: likely duplicate username or email. {e}", "danger")
    except Exception as e:
        db.session.rollback()
        flash(f"Error importing users: {str(e)}", "danger")
    return redirect(url_for('import_export.import_export_page'))

@import_export_bp.route('/import-proxies', methods=['POST'])
def import_proxies():
    file = request.files.get('file')
    if not file:
        flash("No file uploaded", "danger")
        return redirect(url_for('import_export.import_export_page'))

    try:
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        reader = csv.DictReader(stream)
        count = 0
        for row in reader:
            proxy = Proxy(
                username=row['username'].strip(),
                password=row['password'].strip(),
                host=row['host'].strip(),
                port=row['port'].strip()
            )
            db.session.add(proxy)
            count += 1
        db.session.commit()
        flash(f"{count} proxies imported successfully.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error importing proxies: {str(e)}", "danger")
    return redirect(url_for('import_export.import_export_page'))

# ---------- TEMPLATES ----------
@import_export_bp.route('/template/users')
def download_users_template():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['username', 'email', 'password', 'session_limit'])
    writer.writerow(['testuser', 'test@example.com', 'hashed_password_here', '1'])
    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode()), mimetype='text/csv',
                     download_name='users_template.csv', as_attachment=True)

@import_export_bp.route('/template/proxies')
def download_proxies_template():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['username', 'password', 'host', 'port'])
    writer.writerow(['proxyuser', 'proxypass', '123.45.67.89', '8080'])
    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode()), mimetype='text/csv',
                     download_name='proxies_template.csv', as_attachment=True)
