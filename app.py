from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import current_user, logout_user
from flask_wtf.csrf import CSRFProtect
import os
from datetime import datetime, timedelta, timezone

# Import extensions from the extensions file
from extensions import db, login_manager
# Import Admin model to avoid NameError in logout route
from models.admin import Admin

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    
    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    
    # Load configuration
    app.config.from_object('config.Config')
    
    # Set database URI if not already set
    if not app.config.get('SQLALCHEMY_DATABASE_URI'):
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.instance_path, 'parking.db')
    
    # Set secret key if not already set
    if not app.config.get('SECRET_KEY'):
        app.config['SECRET_KEY'] = 'dev-key-for-vehicle-parking-system'
    
    # Initialize CSRF protection
    csrf = CSRFProtect(app)
    
    # Configure session settings to prevent persistence beyond browser close
    app.config['SESSION_PERMANENT'] = False  # Sessions expire when browser is closed
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)  # Sessions expire after 30 minutes of inactivity
    
    # Initialize plugins
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'user.login'  # Set login view for redirect to user login by default
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "info"
    login_manager.session_protection = "strong"  # Helps prevent session cookie hijacking
    login_manager.remember_cookie_duration = timedelta(days=1)  # Remember me cookies last for 1 day
    
    # Configure separate login views for admin and user
    login_manager.blueprint_login_views = {
        'admin': 'admin.login',
        'user': 'user.login'
    }
    
    # Register blueprints
    from routes.admin_routes import admin_bp
    from routes.user_routes import user_bp
    
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(user_bp, url_prefix='/user')
    
    # Create an auth blueprint for login/register
    from flask import Blueprint
    auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
    
    @auth_bp.route('/login', methods=['GET', 'POST'])
    def login():
        # Logout any current session before redirecting
        logout_user()
        
        # Redirect to appropriate login page based on user type
        if request.args.get('type') == 'admin':
            return redirect(url_for('admin.login'))
        else:
            return redirect(url_for('user.login'))
    
    @auth_bp.route('/register', methods=['GET', 'POST'])
    def register():
        return redirect(url_for('user.register'))
    
    @auth_bp.route('/logout')
    def logout():
        # Check if user is authenticated before trying to log out
        if current_user.is_authenticated:
            if isinstance(current_user, Admin):
                return redirect(url_for('admin.logout'))
            else:
                return redirect(url_for('user.logout'))
        else:
            # If not authenticated, just redirect to the index page
            return redirect(url_for('index'))
    
    app.register_blueprint(auth_bp)
    
    # Create database tables and seed data within app context
    with app.app_context():
        # Import models here to avoid circular imports
        from models.admin import Admin
        from models.user import User
        from models.parking_lot import ParkingLot
        from models.parking_spot import ParkingSpot
        from models.booking import Booking
        
        db.create_all()
        
        # Create admin user if not exists
        admin = Admin.query.filter_by(username='admin').first()
        if not admin:
            admin = Admin(username='admin', password='admin123')
            db.session.add(admin)
            db.session.commit()
            print("Admin user created successfully")
        
        # Create test user if not exists (for development)
        test_user = User.query.filter_by(username='user').first()
        if not test_user:
            test_user = User(
                username='user',
                email='user@example.com',
                password='user123',
                first_name='Test',
                last_name='User',
                phone='1234567890'
            )
            db.session.add(test_user)
            db.session.commit()
            print("Test user created successfully")
        
        # Create sample parking lot if not exists (for development)
        if not ParkingLot.query.first():
            # Create a sample parking lot
            parking_lot = ParkingLot(
                name='Main Street Parking',
                address='123 Main Street',
                pin_code='10001',
                price=2.50,  # Using price parameter which will set hourly_rate internally
                total_spots=10,
                available_spots=10
            )
            db.session.add(parking_lot)
            db.session.commit()
            
            # Create sample parking spots
            for i in range(1, 11):
                spot_type = 'standard'
                if i == 1:
                    spot_type = 'disabled'
                elif i == 2:
                    spot_type = 'electric'
                
                spot = ParkingSpot(
                    lot_id=parking_lot.id,
                    spot_number=i,
                    spot_type=spot_type
                )
                db.session.add(spot)
            db.session.commit()
            print("Sample parking lot and spots created successfully")
    
    # Route redirecting to appropriate dashboard based on user type
    @app.route('/')
    def index():
        # Display landing page regardless of authentication status
        # This prevents auto-redirect to dashboard when session cookies exist
        return render_template('index.html')
    
    # Add routes for the main sections accessible without login
    @app.route('/about')
    def about():
        return render_template('about.html')
        
    @app.route('/contact')
    def contact():
        return render_template('contact.html')
    
    # Create blueprint for main pages
    main_bp = Blueprint('main', __name__)
    
    @main_bp.route('/index')
    def index():
        return render_template('index.html')
    
    @main_bp.route('/about')
    def about():
        return render_template('about.html')
        
    @main_bp.route('/contact')
    def contact():
        return render_template('contact.html')
    
    app.register_blueprint(main_bp)
    
    # Error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('shared/404.html'), 404
    
    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('shared/500.html'), 500
    
    @app.context_processor
    def inject_now():
        """Add current time to all templates"""
        return {'now': datetime.now(timezone.utc)}
    
    return app

# Run the application if executed directly
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)