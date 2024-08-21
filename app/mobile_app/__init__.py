from flask import Blueprint

mobile_app_bp = Blueprint('mobile_app', __name__)

from . import routes