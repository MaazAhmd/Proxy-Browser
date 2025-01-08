from flask import Flask, render_template
from models import db, User, Proxy, Admin
from flask_login import LoginManager
from dotenv import load_dotenv
import os
from flask_migrate import Migrate

from auth import auth_bp
from users import users_bp
from proxy import proxies_bp
from groups import groups_bp

app = Flask(__name__)

load_dotenv()

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

db.init_app(app)
migrate = Migrate(app, db)

with app.app_context():
    db.create_all()


login_manager = LoginManager(app)

# Configure LoginManager
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'warning'


@login_manager.user_loader
def load_user(admin_id):
    return Admin.query.get(admin_id)


# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(users_bp, url_prefix='/users')
app.register_blueprint(proxies_bp, url_prefix='/proxy')
app.register_blueprint(groups_bp, url_prefix='/groups')


@app.route('/')
def index():
    num_users = User.query.count()
    num_proxies = Proxy.query.count()
    return render_template('dashboard.html', num_users=num_users, num_proxies=num_proxies)


if __name__ == '__main__':
    app.run(debug=True)
