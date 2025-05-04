from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import current_user
import os
from datetime import datetime, timedelta

# Import extensions from the extensions file
from extensions import db, login_manager

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
    
    # Initialize plugins
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'user_bp.login'  # Set login view for redirect
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "info"
    
    # Import models
    with app.app_context():
        from models import Admin, User, ParkingLot, ParkingSpot, Booking
    
    # Register blueprints
    from routes.admin_routes import admin_bp
    from routes.user_routes import user_bp
    
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(user_bp, url_prefix='/user')
    
    # Create database tables and seed data within app context
    with app.app_context():
        db.create_all()
        
        # Create admin user if not exists
        admin = Admin.query.filter_by(username='admin').first()
        if not admin:
            admin = Admin(username='admin', password='admin123')
            db.session.add(admin)
            db.session.commit()
            print("Admin user created successfully")
        
        # Create test user if not exists (for development)
        if app.config.get('FLASK_ENV') == 'development':
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
        if app.config.get('FLASK_ENV') == 'development' and not ParkingLot.query.first():
            # Create a sample parking lot
            parking_lot = ParkingLot(
                name='Main Street Parking',
                address='123 Main Street',
                pin_code='10001',
                postcode_level='Downtown',
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
                    spot_id=f'A-{i}',
                    parking_lot_id=parking_lot.id,
                    spot_type=spot_type,
                    is_available=True
                )
                db.session.add(spot)
            db.session.commit()
            print("Sample parking lot and spots created successfully")
    
    # Route redirecting to appropriate dashboard based on user type
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            if isinstance(current_user, Admin):
                return redirect(url_for('admin_bp.dashboard'))
            else:
                return redirect(url_for('user_bp.dashboard'))
        return render_template('shared/base.html')
    
    # Authentication routes
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        # Check if user is trying to login as admin
        if 'admin' in request.path or request.args.get('type') == 'admin':
            return redirect(url_for('admin_bp.login'))
        else:
            return redirect(url_for('user_bp.login'))
    
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        return redirect(url_for('user_bp.register'))
    
    @app.route('/logout')
    def logout():
        if 'admin' in request.path or request.args.get('type') == 'admin':
            return redirect(url_for('admin_bp.logout'))
        else:
            return redirect(url_for('user_bp.logout'))
    
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
        return {'now': datetime.utcnow()}
    
    return app

# Run the application if executed directly
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)