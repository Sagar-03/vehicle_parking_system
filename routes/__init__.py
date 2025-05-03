from flask import Blueprint

admin_bp = Blueprint('admin', __name__)
user_bp = Blueprint('user', __name__)

from . import admin_routes, user_routes
