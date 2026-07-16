from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config
from app.semana_protecao_dados import bp as spd_bp
from datetime import datetime
import os

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = "Por favor, faça login para acessar esta página."
login_manager.login_message_category = "info"

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    app.register_blueprint(spd_bp)
    
    db.init_app(app)
    login_manager.init_app(app)

    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    from app.auth.routes import auth
    from app.documents.routes import documents
    from app.admin.routes import admin

    app.register_blueprint(auth)
    app.register_blueprint(documents)
    app.register_blueprint(admin)

    @app.before_request
    def track_pageview():
        if request.method != 'GET':
            return
        path = request.path
        if path.startswith('/static') or path.startswith('/reports/acessos'):
            return
        from app.models import PageView
        from flask_login import current_user
        user_id = current_user.id if current_user.is_authenticated else None
        pv = PageView(path=path, user_id=user_id, method=request.method)
        db.session.add(pv)
        db.session.commit()

    @app.context_processor
    def inject_sectors():
        from app.models import Sector
        return dict(sectors=Sector.query.all())

    return app
