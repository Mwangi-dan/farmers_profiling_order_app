import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL_POSTGRES')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = 'your_jwt_secret_key'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)  # 1 hour
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)  # 30 days
    JWT_TOKEN_LOCATION = ['cookies']
    JWT_ACCESS_COOKIE_PATH = '/'
    JWT_REFRESH_COOKIE_PATH = '/auth/token/refresh'
    JWT_COOKIE_SECURE = False  # Should be True in production with HTTPS
    WTF_CSRF_ENABLED = True
    WTF_CSRF_SECRET_KEY = 'your_csrf_secret_key'
    SESSION_COOKIE_DOMAIN = False
    DEBUG = True  
    JWT_COOKIE_CSRF_PROTECT = False
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'app', 'static', 'images', 'uploads')
    PRODUCT_UPLOAD_FOLDER = os.path.join(BASE_DIR, 'app', 'static', 'images', 'product_uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # Max file size: 16MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

ISSUE_STATUS = ['Open', 'In Progress', 'Resolved', 'Closed']
ORDER_STATUS = ['Pending', 'Processing', 'Shipped', 'Delivered', 'Cancelled']