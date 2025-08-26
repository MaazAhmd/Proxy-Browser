import json
from flask import Blueprint, render_template, request, redirect, url_for, jsonify, flash
from sqlalchemy.exc import SQLAlchemyError

from models import db, DialerUser, CommandLog

dialer_bp = Blueprint("dialer", __name__, template_folder="templates")

# Index - list all users
@dialer_bp.route("/")
def index():
    # db.metadata.drop_all(
    #     bind=db.engine,
    #     tables=[DialerUser.__table__, CommandLog.__table__]
    # )
    # db.create_all()
    search_query = request.args.get("search", "").strip()
    if search_query:
        users = DialerUser.query.filter(
            DialerUser.username.ilike(f"%{search_query}%")
        ).all()
    else:
        users = DialerUser.query.all()

    return render_template("dialer/index.html", users=users, search_query=search_query)


# Add user
@dialer_bp.route("/add", methods=["GET", "POST"])
def add_user():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        new_user = DialerUser(username=username, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for("dialer.index"))

    return render_template("dialer/add_user.html")

# Login - return token if correct
@dialer_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    user = DialerUser.query.filter_by(username=username, password=password).first()
    if user:
        if not user.match_type or not user.match_value:
            return jsonify({"message": "User profile incomplete. Please ask your administrator to set target IPs/Country and Try Again."}), 400

        token = user.generate_token()
        db.session.commit()
        return jsonify({"message": "Login successful", "token": token})
    return jsonify({"message": "Invalid credentials. Please enter correct username/password and try again. "}), 401

# Add command (button clicks)
@dialer_bp.route("/add_command/<int:user_id>/<string:command>")
def add_command(user_id, command):
    user = DialerUser.query.get_or_404(user_id)

    log = CommandLog(user_id=user.id, command=command.upper())
    db.session.add(log)
    db.session.commit()

    return redirect(url_for("dialer.index"))

# Logs page for a user
@dialer_bp.route("/logs/<int:user_id>")
def view_logs(user_id):
    user = DialerUser.query.get_or_404(user_id)
    logs = CommandLog.query.filter_by(user_id=user.id).order_by(CommandLog.executed_at.desc()).all()
    return render_template("dialer/logs.html", user=user, logs=logs)

# API - Get commands by token
@dialer_bp.route("/actions", methods=["POST"])
def get_commands():
    data = request.get_json()
    token = data.get("token")

    user = DialerUser.query.filter_by(token=token).first()
    if not user:
        return jsonify({"message": "Invalid token"}), 401

    logs = CommandLog.query.filter_by(user_id=user.id).order_by(CommandLog.executed_at).all()
    commands = [{"command": log.command, "time": log.executed_at.isoformat(), "result": log.result, 'command_id': log.id} for log in logs]

    return jsonify({"commands": commands})


@dialer_bp.route("/results", methods=["POST"])
def receive_result():
    data = request.get_json()
    token = data.get("token")
    result_message = data.get("result")

    print("Received Result Response: ", data, result_message)

    if not token or not result_message:
        return jsonify({"ok": False, "error": "Missing token or result"}), 400

    # Find the user by token
    user = DialerUser.query.filter_by(token=token).first()
    if not user:
        return jsonify({"ok": False, "error": "Invalid token"}), 401

    status = None
    command_id = None
    message = None

    try:
        # Case 1: COMPLETE 12
        if result_message.startswith("COMPLETE"):
            _, command_id_str = result_message.split(" ", 1)
            status = "COMPLETE"
            command_id = int(command_id_str.strip())

        # Case 2: FAILED 12: Some error message
        elif result_message.startswith("FAILED"):
            parts = result_message.split(" ", 1)[1]  # get everything after "FAILED "
            command_id_str, msg = parts.split(":", 1)
            status = "FAILED"
            command_id = int(command_id_str.strip())
            message = msg.strip()
        else:
            print("Invalid Result Format")
            return jsonify({"ok": False, "error": "Invalid result format"}), 400

    except Exception as e:
        print(f"Parsing Error: {str(e)}")
        return jsonify({"ok": False, "error": f"Parsing error: {str(e)}"}), 400

    # Find the command log
    log = CommandLog.query.filter_by(id=command_id, user_id=user.id).first()
    if not log:
        return jsonify({"ok": False, "error": "Command not found"}), 404

    # Update result
    if status == "COMPLETE":
        log.result = "COMPLETE"
    elif status == "FAILED":
        log.result = f"FAILED: {message}"

    db.session.commit()
    return jsonify({"ok": True, "message": f"Result updated for command {command_id}"})

APPS_LIST = ["Vonage", "RingCentral", "8x8 Work", "Dialpad", "OpenPhone", "Grasshopper", "Zoom", 'Chrome']
COUNTRIES = ["USA", "Saudi Arabia", "UAE", "Australia", "UK"]


@dialer_bp.route("/<int:user_id>/manage", methods=["GET", "POST"])
def manage_user(user_id):
    user = DialerUser.query.get_or_404(user_id)

    if request.method == "POST":
        # Apps selection
        selected_apps = request.form.getlist("apps")
        user.apps = json.dumps(selected_apps)

        # Target matching
        match_type = request.form.get("match_type")
        user.match_type = match_type

        if match_type == "country":
            country = request.form.get("country")
            user.match_value = json.dumps([country]) if country else json.dumps([])
        elif match_type == "ip":
            raw_ips = request.form.get("ips", "")
            ips = [ip.strip() for ip in raw_ips.replace("\n", ",").split(",") if ip.strip()]
            user.match_value = json.dumps(ips)

        # Monitoring status
        monitoring_status = request.form.get("monitoring_status")
        user.monitoring = True if monitoring_status == "start" else False

        db.session.commit()
        flash("User settings updated successfully!", "success")
        return redirect(url_for("dialer.index"))

    # Parse existing values for display
    current_apps = json.loads(user.apps or "[]")
    current_match_type = user.match_type
    current_match_value = json.loads(user.match_value or "[]")
    monitoring_enabled = getattr(user, "monitoring_enabled", False)

    return render_template(
        "dialer/manage_user.html",
        user=user,
        apps=APPS_LIST,
        countries=COUNTRIES,
        current_apps=current_apps,
        current_match_type=current_match_type,
        current_match_value=current_match_value,
        monitoring_enabled=monitoring_enabled,
    )


@dialer_bp.route("/targets", methods=["POST"])
def get_targets():
    data = request.get_json()
    token = data.get("token")

    user = DialerUser.query.filter_by(token=token).first()
    if not user:
        return jsonify({"message": "Invalid token"}), 401

    # Prepare targets data
    targets = {
        "apps": user.apps if user.apps else [],
        "target_type": user.match_type,   # "country" or "ip"
        "target_value": None
    }

    if user.match_type == "country":
        targets["target_value"] = user.match_value
    elif user.match_type == "ip":
        # stored as JSON string -> parse into list
        try:
            targets["target_value"] = json.loads(user.match_value)
        except Exception:
            targets["target_value"] = []

    return jsonify({"targets": targets})


@dialer_bp.route("/monitoring", methods=["POST"])
def monitoring_status():
    data = request.get_json()
    token = data.get("token")
    status_message = data.get("status")  # client sends "ACTIVE", "INACTIVE", "STOPPED BY USER", "Error: ..."

    user = DialerUser.query.filter_by(token=token).first()
    if not user:
        return jsonify({"message": "Invalid token"}), 401

    # Save the client-reported status
    if status_message:
        user.monitoring_status = status_message
        db.session.commit()

    # Server always responds with monitoring = True/False (admin setting)
    return jsonify({
        "monitoring": bool(user.monitoring),   # server decides this
        "status": user.monitoring_status       # latest client-reported status
    })


@dialer_bp.route("/missing_apps", methods=["POST"])
def update_missing_apps():
    data = request.get_json()
    token = data.get("token")
    missing_apps = data.get("missing_apps")  # should be a list

    if not token or not missing_apps:
        return jsonify({"error": "Token and missing_apps are required"}), 400

    try:
        user = DialerUser.query.filter_by(token=token).first()
        if not user:
            return jsonify({"error": "Invalid token"}), 401

        # Assuming DialerUser has a column named 'apps' (JSON/Text)
        # If it's JSON -> store list directly, else store comma-separated string
        if isinstance(missing_apps, list):
            user.missing_apps = ",".join(missing_apps)
        else:
            user.missing_apps = str(missing_apps)

        db.session.commit()

        return jsonify({"message": "Missing apps updated", "apps": user.missing_apps}), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

