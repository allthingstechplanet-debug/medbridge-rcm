from flask import Flask
from flask_login import LoginManager
from flask_mail import Mail
from .models import db, User
from config import Config

mail = Mail()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Init extensions
    db.init_app(app)
    mail.init_app(app)
    login_manager.init_app(app)

    # Register blueprints (routes)
    from .routes.auth import auth_bp
    from .routes.dashboard import dashboard_bp
    from .routes.prior_auth import prior_auth_bp
    from .routes.denial import denial_bp
    from .routes.patient import patient_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(prior_auth_bp)
    app.register_blueprint(denial_bp)
    app.register_blueprint(patient_bp)

    # Create tables on first run
    with app.app_context():
        db.create_all()

    return app
