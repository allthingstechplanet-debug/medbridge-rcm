import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    # Init extensions
    db.init_app(app)
    login_manager.init_app(app)

    # Register blueprints
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

from .models import User

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
