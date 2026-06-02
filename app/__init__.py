from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config
import os

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = "Por favor, faça login para acessar esta página."
login_manager.login_message_category = "info"

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)

    # Ensure upload folder exists
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    # Register Blueprints
    from app.auth.routes import auth
    from app.documents.routes import documents
    from app.admin.routes import admin
    # from app.main.routes import main # We can add a main blueprint later if needed

    app.register_blueprint(auth)
    app.register_blueprint(documents)
    app.register_blueprint(admin)

    @app.context_processor
    def inject_sectors():
        from app.models import Sector
        return dict(sectors=Sector.query.all())

    return app
