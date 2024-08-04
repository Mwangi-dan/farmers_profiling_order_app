from flask import Flask, request, redirect, url_for, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from app.models import db
from dotenv import load_dotenv
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect, CSRFError
from flask_jwt_extended import JWTManager
import os
from .filters import time_since


load_dotenv()

migrate = Migrate()
csrf = CSRFProtect()
jwt = JWTManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')
    app.config['GOOGLE_MAPS_API_KEY'] = os.getenv('GOOGLE_MAPS_API_KEY')

    migrate = Migrate(app, db, render_as_batch=True)
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    jwt.init_app(app)
    CORS(app)

    app.jinja_env.filters['time_since'] = time_since

    @app.route('/')
    def index():
        return redirect(url_for('auth.login'))

    @app.before_request
    def before_request():
        token = request.cookies.get('access_token')
        if token:
            request.headers = {'Authorization': f'Bearer {token}'}

    
    app.config['JWT_SECRET_KEY'] = 'your_secret_key'
    jwt.init_app(app)

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return unauthorized_error("Token has expired")

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return unauthorized_error("Invalid token")

    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        return render_template('csrf_error.html', reason=e.description), 400
    
    @app.errorhandler(401)
    def unauthorized_error(error):
        return render_template('errors/token_expired.html'), 401
        

    @app.context_processor
    def inject_active_endpoint():
        return {'active_endpoint': request.endpoint}

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
