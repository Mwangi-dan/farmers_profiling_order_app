from flask import Flask, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from app.models import db
from dotenv import load_dotenv
from flask_migrate import Migrate
import os


load_dotenv()

migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    db.init_app(app)
    migrate.init_app(app, db)
    jwt = JWTManager(app)
    CORS(app)

    @app.route('/')
    def index():
        return redirect(url_for('auth.login'))

    @app.before_request
    def before_request():
        token = request.cookies.get('access_token')
        if token:
            request.headers = {'Authorization': f'Bearer {token}'}
    

    from .auth.routes import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    from .admin.routes import admin as admin_blueprint
    app.register_blueprint(admin_blueprint, url_prefix='/admin')

    '''
    from .ussd.routes import ussd as ussd_blueprint
    app.register_blueprint(ussd_blueprint, url_prefix='/ussd')
    '''
    with app.app_context():
        db.create_all()

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
