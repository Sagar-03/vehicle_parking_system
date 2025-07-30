from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()


@login_manager.user_loader
def load_user(user_id):
    from models.admin import Admin
    from models.user import User
    
    # Try loading as admin first
    admin = Admin.query.get(int(user_id))
    if admin:
        return admin
    
    # If not an admin, try loading as regular user
    return User.query.get(int(user_id))