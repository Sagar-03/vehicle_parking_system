from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, login_user, logout_user, current_user
from extensions import db
from models.admin import Admin
from models.user import User
from models.parking_lot import ParkingLot
from models.parking_spot import ParkingSpot
from models.booking import Booking
from models.vehicle import Vehicle
from datetime import datetime, timedelta, timezone
from functools import wraps
# Using Flask-WTF for CSRF protection and Flask integration
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, DecimalField, IntegerField, BooleanField, SubmitField, SelectField, TextAreaField
from wtforms.validators import DataRequired, NumberRange, Optional

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Form classes
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(message="Username is required")])
    password = PasswordField('Password', validators=[DataRequired(message="Password is required")])
    submit = SubmitField('Login')

class ParkingLotForm(FlaskForm):
    name = StringField('Parking Lot Name', validators=[DataRequired()])
    location = StringField('Location', validators=[DataRequired()])
    address = StringField('Address', validators=[DataRequired()])
    pin_code = StringField('PIN Code', validators=[DataRequired()])
    total_spots = IntegerField('Total Parking Spots', validators=[DataRequired(), NumberRange(min=1)])
    hourly_rate = DecimalField('Hourly Rate ($)', validators=[DataRequired(), NumberRange(min=0)])
    opening_time = StringField('Opening Time', validators=[DataRequired()])
    closing_time = StringField('Closing Time', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[Optional()])
    is_active = BooleanField('Active', default=True)
    num_rows = IntegerField('Number of Rows', validators=[DataRequired(), NumberRange(min=1)])
    num_cols = IntegerField('Spots per Row', validators=[DataRequired(), NumberRange(min=1)])
    submit = SubmitField('Add Parking Lot')

# Custom decorator to check if the user is an admin
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is authenticated first
        if not current_user.is_authenticated:
            flash('Please login to access this page.', 'warning')
            return redirect(url_for('admin.login'))
        
        # Then check if the user is an Admin instance
        if not isinstance(current_user._get_current_object(), Admin):
            # Special case for admin username
            if current_user.username == 'admin':
                # This is a special case - the admin user is authenticated but not recognized as Admin type
                # Let's attempt to find or create the admin in the database
                admin = Admin.query.filter_by(username='admin').first()
                if not admin:
                    # Create admin user if it doesn't exist
                    admin = Admin(username='admin', password='admin123')
                    db.session.add(admin)
                    db.session.commit()
                
                # Force logout and redirect to login
                logout_user()
                flash('Please login as admin again.', 'warning')
                return redirect(url_for('admin.login'))
            else:
                flash('Access denied. Admin privileges required.', 'danger')
                return redirect(url_for('admin.login'))
        
        return f(*args, **kwargs)
    return decorated_function

# Admin login
@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    # Clear any existing sessions first to ensure fresh login
    logout_user()
    
    form = LoginForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            username = form.username.data
            password = form.password.data
            
            # Debug - print the admin username entered
            print(f"Admin login attempt for username: {username}")
            
            # Get admin user
            admin = Admin.query.filter_by(username=username).first()
            
            # Special handling for the admin user
            if username == 'admin' and password == 'admin123':
                # If admin doesn't exist in DB for some reason, create it
                if not admin:
                    admin = Admin(username='admin', password='admin123')
                    db.session.add(admin)
                    db.session.commit()
                    admin = Admin.query.filter_by(username='admin').first()
                
                # Login the admin user
                login_user(admin)
                flash('Admin login successful!', 'success')
                return redirect(url_for('admin.dashboard'))
            elif admin and admin.verify_password(password):
                login_user(admin)
                flash('Login successful!', 'success')
                return redirect(url_for('admin.dashboard'))
            else:
                flash('Invalid username or password.', 'danger')
        else:
            flash('Form validation failed. Please check your inputs.', 'danger')
    
    return render_template('admin/login.html', form=form)

# Admin logout
@admin_bp.route('/logout')
@login_required
@admin_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('admin.login'))

# Admin dashboard
@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    # Count metrics for the dashboard
    parking_lot_count = ParkingLot.query.count()
    total_spots = ParkingSpot.query.count()
    available_spots = ParkingSpot.query.filter_by(is_available=True).count()
    occupied_spots = ParkingSpot.query.filter_by(is_available=False).count()
    
    # Get recent activities (bookings)
    recent_activities = []
    recent_bookings = Booking.query.order_by(Booking.parking_timestamp.desc()).limit(10).all()
    
    for booking in recent_bookings:
        user = User.query.get(booking.user_id)
        spot = ParkingSpot.query.get(booking.parking_spot_id)
        
        if user and spot:
            activity_type = "Check Out" if booking.leaving_timestamp else "Check In"
            timestamp = booking.leaving_timestamp or booking.parking_timestamp
            
            recent_activities.append({
                "description": f"{activity_type}: {user.username} at spot {spot.spot_id}",
                "timestamp": timestamp.strftime('%Y-%m-%d %H:%M')
            })
    
    # Get parking spots for overview
    parking_spots = []
    for spot in ParkingSpot.query.limit(50).all():  # Limit to avoid too many spots in overview
        spot_data = {
            "id": spot.id,
            "spot_number": spot.spot_number,
            "is_occupied": not spot.is_available
        }
        
        if not spot.is_available:
            booking = spot.current_booking()
            if booking:
                user = User.query.get(booking.user_id)
                if user:
                    spot_data["user"] = {"username": user.username}
        
        parking_spots.append(spot_data)
    
    # Get charts data
    dates = [(datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7, 0, -1)]
    
    # Occupancy rates per day (last 7 days)
    occupancy_rates = []
    for date in dates:
        # Simulate occupancy rate for now
        # In a real application, you would calculate this from booking data
        import random
        occupancy_rates.append(random.randint(50, 90))
    
    # Revenue per day (last 7 days)
    daily_revenue = []
    for date in dates:
        # Simulate daily revenue for now
        daily_revenue.append(random.randint(500, 2000))
    
    # Get list of users
    users = User.query.all()
    
    # Get list of parking lots
    parking_lots = ParkingLot.query.all()
    
    # System logs (for logs tab)
    system_logs = []
    # In a real app, you would fetch actual logs from a logs table
    
    return render_template('admin/admin_dashboard.html',
                           parking_lot_count=parking_lot_count,
                           available_spots=available_spots,
                           occupied_spots=occupied_spots,
                           recent_activities=recent_activities,
                           parking_spots=parking_spots,
                           users=users,
                           parking_lots=parking_lots,
                           system_logs=system_logs,
                           occupancy_dates=dates,
                           occupancy_rates=occupancy_rates,
                           revenue_dates=dates,
                           daily_revenue=daily_revenue)

# Add new parking lot
@admin_bp.route('/add_parking_lot', methods=['GET', 'POST'])
@login_required
@admin_required
def add_parking_lot():
    form = ParkingLotForm(request.form)
    
    if request.method == 'POST' and form.validate():
        # Create new parking lot
        new_lot = ParkingLot(
            name=form.name.data,
            address=form.address.data,
            pin_code=form.pin_code.data,
            price=float(form.hourly_rate.data),
            total_spots=form.total_spots.data
        )
        
        db.session.add(new_lot)
        db.session.commit()
        
        # Create parking spots for the lot
        num_rows = form.num_rows.data
        num_cols = form.num_cols.data
        
        for i in range(1, form.total_spots.data + 1):
            # Set some spots as special types (every 10th spot is disabled, every 15th is electric)
            spot_type = 'standard'
            if i % 10 == 0:
                spot_type = 'disabled'
            elif i % 15 == 0:
                spot_type = 'electric'
                
            new_spot = ParkingSpot(
                lot_id=new_lot.id,
                spot_number=i,
                spot_type=spot_type
            )
            db.session.add(new_spot)
        
        db.session.commit()
        
        # Update available spots count in the lot
        new_lot.update_available_spots()
        
        flash(f'Parking lot "{form.name.data}" with {form.total_spots.data} spots added successfully!', 'success')
        return redirect(url_for('admin.dashboard'))
    
    return render_template('admin/add_parking_lot.html', form=form)

# View all parking spots
@admin_bp.route('/view_parking_spots')
@login_required
@admin_required
def view_parking_spots():
    # Get all parking lots
    lots = ParkingLot.query.all()
    
    # Get filter parameters
    lot_id = request.args.get('lot_id', type=int)
    status = request.args.get('status')
    spot_type = request.args.get('type')
    
    # Base query
    query = ParkingSpot.query
    
    # Apply filters
    if lot_id:
        query = query.filter_by(lot_id=lot_id)
    
    if status:
        if status == 'available':
            query = query.filter_by(is_available=True)
        elif status == 'occupied':
            query = query.filter_by(is_available=False)
    
    if spot_type and spot_type != 'all':
        query = query.filter_by(spot_type=spot_type)
    
    # Get spots with applied filters
    spots = query.all()
    
    # Calculate stats
    total_spots = len(spots)
    available_spots = sum(1 for spot in spots if spot.is_available)
    occupied_spots = total_spots - available_spots
    
    return render_template('admin/view_parking_spots.html', 
                          lots=lots,
                          spots=spots,
                          total_spots=total_spots,
                          available_spots=available_spots,
                          occupied_spots=occupied_spots,
                          selected_lot_id=lot_id)

# View statistics
@admin_bp.route('/statistics')
@login_required
@admin_required
def statistics():
    # Get all bookings
    bookings = Booking.query.all()
    
    # Get date range parameters
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    if start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        except ValueError:
            start_date = datetime.now() - timedelta(days=30)
            end_date = datetime.now()
    else:
        # Default to last 30 days
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()
    
    # Filter bookings by date range
    filtered_bookings = [b for b in bookings if start_date <= b.parking_timestamp <= end_date]
    
    # Calculate statistics
    total_bookings = len(filtered_bookings)
    total_revenue = sum(b.total_cost or 0 for b in filtered_bookings if b.total_cost)
    
    # Calculate occupancy rate
    total_spots = ParkingSpot.query.count()
    if total_spots > 0:
        average_occupancy = (ParkingSpot.query.filter_by(is_available=False).count() / total_spots) * 100
    else:
        average_occupancy = 0
    
    # Get data for charts
    # In a real app, you would aggregate this data more efficiently
    
    return render_template('admin/statistics.html',
                          total_bookings=total_bookings,
                          total_revenue=total_revenue,
                          average_occupancy=average_occupancy,
                          start_date=start_date,
                          end_date=end_date)

# View users
@admin_bp.route('/view_user')
@login_required
@admin_required
def view_user():
    users = User.query.all()
    # Flask-WTF automatically adds csrf_token to template context when using render_template
    return render_template('admin/view_user.html', users=users)

# Delete user
@admin_bp.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    # Check if user has active bookings
    active_bookings = Booking.query.filter_by(user_id=user_id, leaving_timestamp=None).count()
    
    if active_bookings > 0:
        flash(f'Cannot delete user. User has {active_bookings} active booking(s).', 'danger')
        return redirect(url_for('admin.view_user'))
    
    # It's safe to delete
    db.session.delete(user)
    db.session.commit()
    
    flash('User deleted successfully.', 'success')
    return redirect(url_for('admin.view_user'))

# API endpoints for charts
@admin_bp.route('/api/lot_stats')
@login_required
@admin_required
def lot_stats():
    lots = ParkingLot.query.all()
    stats = []
    
    for lot in lots:
        stats.append({
            'name': lot.name,
            'total': lot.total_spots,
            'available': lot.available_spots,
            'occupied': lot.occupied_spots_count()
        })
    
    return jsonify(stats)

# API endpoint for parking spot status
@admin_bp.route('/api/spot_status/<int:spot_id>', methods=['POST'])
@login_required
@admin_required
def update_spot_status(spot_id):
    spot = ParkingSpot.query.get_or_404(spot_id)
    data = request.json
    
    if 'status' in data:
        if data['status'] == 'maintenance':
            # Can only set to maintenance if not occupied
            if not spot.is_available:
                booking = spot.current_booking()
                if booking:
                    return jsonify({'success': False, 'message': 'Cannot set to maintenance. Spot is occupied.'})
            
            spot.status = 'M'  # Maintenance
            spot.is_available = False
        elif data['status'] == 'available':
            # Can only set to available if not occupied
            if not spot.is_available:
                booking = spot.current_booking()
                if booking:
                    return jsonify({'success': False, 'message': 'Cannot set to available. Spot is occupied.'})
            
            spot.status = 'A'  # Available
            spot.is_available = True
        
        db.session.commit()
        
        # Update parent lot's available spots count
        spot.parking_lot.update_available_spots()
        
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'message': 'Invalid data'})

# Manually mark spot as occupied
@admin_bp.route('/mark_spot_occupied', methods=['POST'])
@login_required
@admin_required
def mark_spot_occupied():
    spot_id = request.form.get('spot_id')
    vehicle_reg = request.form.get('vehicle_reg')
    
    if not spot_id or not vehicle_reg:
        flash('Spot ID and Vehicle Registration are required.', 'danger')
        return redirect(url_for('admin.view_parking_spots'))
    
    # Get the spot
    spot = ParkingSpot.query.get_or_404(spot_id)
    
    # Check if spot is already occupied
    if not spot.is_available:
        flash('This spot is already occupied.', 'danger')
        return redirect(url_for('admin.view_parking_spots'))
    
    # Create a manual booking (without user)
    booking = Booking(
        user_id=1,  # Admin user ID or system user
        parking_spot_id=spot.id,
        vehicle_reg=vehicle_reg,
        booking_status='admin_marked'
    )
    
    db.session.add(booking)
    
    # Update spot status
    spot.is_available = False
    db.session.add(spot)
    
    db.session.commit()
    
    flash(f'Spot {spot.spot_number} has been marked as occupied with vehicle {vehicle_reg}.', 'success')
    return redirect(url_for('admin.view_parking_spots'))

# Release a parking spot (admin action)
@admin_bp.route('/release_spot', methods=['POST'])
@login_required
@admin_required
def release_spot():
    spot_id = request.form.get('spot_id')
    
    if not spot_id:
        flash('Spot ID is required.', 'danger')
        return redirect(url_for('admin.view_parking_spots'))
    
    # Get the spot
    spot = ParkingSpot.query.get_or_404(spot_id)
    
    # Check if spot is available (can't release an already available spot)
    if spot.is_available:
        flash('This spot is already available.', 'danger')
        return redirect(url_for('admin.view_parking_spots'))
    
    # Find any active booking for this spot
    booking = Booking.query.filter_by(
        parking_spot_id=spot.id, 
        booking_status='active'
    ).first()
    
    if booking:
        # End the booking
        booking.leaving_timestamp = datetime.now(timezone.utc)
        booking.booking_status = 'completed'
        booking.calculate_total_cost()
        db.session.add(booking)
    
    # Update spot status
    spot.is_available = True
    db.session.add(spot)
    
    db.session.commit()
    
    flash(f'Spot {spot.spot_number} has been released and is now available.', 'success')
    return redirect(url_for('admin.view_parking_spots'))

# API endpoints for accessing parking data programmatically
@admin_bp.route('/api/parking_data', methods=['GET'])
@login_required
@admin_required
def api_parking_data():
    """API endpoint for getting parking data."""
    
    # Get query parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    lot_id = request.args.get('lot_id')
    
    # Base query for bookings
    query = db.session.query(Booking)
    
    # Apply filters if provided
    if start_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(Booking.parking_timestamp >= start_date)
        except ValueError:
            return jsonify({'error': 'Invalid start_date format. Use YYYY-MM-DD'}), 400
    
    if end_date:
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
            # Add a day to include the end date fully
            end_date = end_date + timedelta(days=1)
            query = query.filter(Booking.parking_timestamp < end_date)
        except ValueError:
            return jsonify({'error': 'Invalid end_date format. Use YYYY-MM-DD'}), 400
    
    if lot_id:
        try:
            lot_id = int(lot_id)
            # Join with parking spot to filter by lot_id
            query = query.join(ParkingSpot, Booking.parking_spot_id == ParkingSpot.id)\
                         .filter(ParkingSpot.lot_id == lot_id)
        except ValueError:
            return jsonify({'error': 'Invalid lot_id. Must be an integer'}), 400
    
    # Execute query
    bookings = query.all()
    
    # Format results
    result = []
    for booking in bookings:
        spot = ParkingSpot.query.get(booking.parking_spot_id) if booking.parking_spot_id else None
        lot = ParkingLot.query.get(spot.lot_id) if spot else None
        user = User.query.get(booking.user_id)
        vehicle = Vehicle.query.get(booking.vehicle_id) if booking.vehicle_id else None
        
        # Calculate duration and format timestamps
        if booking.leaving_timestamp:
            duration_seconds = (booking.leaving_timestamp - booking.parking_timestamp).total_seconds()
            duration_hours = round(duration_seconds / 3600, 2)
        else:
            duration_hours = None
        
        booking_data = {
            'id': booking.id,
            'user': {
                'id': user.id if user else None,
                'name': f"{user.first_name} {user.last_name}" if user else None,
                'email': user.email if user else None
            },
            'vehicle': {
                'id': vehicle.id if vehicle else None,
                'model': vehicle.model if vehicle else None,
                'license_plate': vehicle.license_plate if vehicle else booking.vehicle_reg,
                'vehicle_type': vehicle.vehicle_type if vehicle else None
            },
            'parking': {
                'spot_id': spot.id if spot else None,
                'spot_number': spot.spot_number if spot else None,
                'lot_id': lot.id if lot else None,
                'lot_name': lot.name if lot else None
            },
            'timestamps': {
                'check_in': booking.parking_timestamp.isoformat() if booking.parking_timestamp else None,
                'check_out': booking.leaving_timestamp.isoformat() if booking.leaving_timestamp else None,
                'duration_hours': duration_hours
            },
            'payment': {
                'amount': booking.total_cost,
                'status': booking.payment_status if hasattr(booking, 'payment_status') else None
            },
            'status': booking.booking_status
        }
        result.append(booking_data)
    
    return jsonify({
        'status': 'success',
        'count': len(result),
        'data': result
    })

@admin_bp.route('/api/parking_stats', methods=['GET'])
@login_required
@admin_required
def api_parking_stats():
    """API endpoint for getting parking statistics."""
    
    # Get query parameters
    period = request.args.get('period', 'day')  # day, week, month
    days = request.args.get('days', '30')
    lot_id = request.args.get('lot_id')
    
    try:
        days = int(days)
        if days <= 0:
            raise ValueError
    except ValueError:
        return jsonify({'error': 'Invalid days parameter. Must be a positive integer'}), 400
    
    # Calculate the start date based on the requested period
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)
    
    # Base query
    query = db.session.query(Booking)
    
    # Filter by date range
    query = query.filter(Booking.parking_timestamp >= start_date, 
                         Booking.parking_timestamp <= end_date)
    
    # Filter by lot if provided
    if lot_id:
        try:
            lot_id = int(lot_id)
            query = query.join(ParkingSpot, Booking.parking_spot_id == ParkingSpot.id)\
                         .filter(ParkingSpot.lot_id == lot_id)
        except ValueError:
            return jsonify({'error': 'Invalid lot_id. Must be an integer'}), 400
    
    # Execute query
    bookings = query.all()
    
    # Initialize statistics
    stats = {
        'period': {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'days': days
        },
        'summary': {
            'total_bookings': len(bookings),
            'total_revenue': sum(booking.total_cost or 0 for booking in bookings),
            'completed_bookings': len([b for b in bookings if b.booking_status == 'completed']),
            'cancelled_bookings': len([b for b in bookings if b.booking_status == 'cancelled']),
            'active_bookings': len([b for b in bookings if b.booking_status == 'active']),
            'avg_booking_duration': 0
        },
        'trends': {}
    }
    
    # Calculate average duration
    completed_bookings = [b for b in bookings if b.leaving_timestamp]
    if completed_bookings:
        total_duration = sum((b.leaving_timestamp - b.parking_timestamp).total_seconds() 
                            for b in completed_bookings)
        avg_duration_hours = (total_duration / len(completed_bookings)) / 3600
        stats['summary']['avg_booking_duration'] = round(avg_duration_hours, 2)
    
    # Generate time-based statistics
    date_format = '%Y-%m-%d'
    if period == 'day':
        # Daily stats
        daily_stats = {}
        for booking in bookings:
            day_key = booking.parking_timestamp.strftime(date_format)
            if day_key not in daily_stats:
                daily_stats[day_key] = {
                    'bookings': 0,
                    'revenue': 0,
                    'completed': 0,
                    'cancelled': 0
                }
            daily_stats[day_key]['bookings'] += 1
            daily_stats[day_key]['revenue'] += booking.total_cost or 0
            if booking.booking_status == 'completed':
                daily_stats[day_key]['completed'] += 1
            elif booking.booking_status == 'cancelled':
                daily_stats[day_key]['cancelled'] += 1
        
        stats['trends']['daily'] = daily_stats
    
    elif period == 'week':
        # Weekly stats
        weekly_stats = {}
        for booking in bookings:
            # Get the week number and year
            week_key = f"{booking.parking_timestamp.strftime('%Y-W%W')}"
            if week_key not in weekly_stats:
                weekly_stats[week_key] = {
                    'bookings': 0,
                    'revenue': 0,
                    'completed': 0,
                    'cancelled': 0
                }
            weekly_stats[week_key]['bookings'] += 1
            weekly_stats[week_key]['revenue'] += booking.total_cost or 0
            if booking.booking_status == 'completed':
                weekly_stats[week_key]['completed'] += 1
            elif booking.booking_status == 'cancelled':
                weekly_stats[week_key]['cancelled'] += 1
        
        stats['trends']['weekly'] = weekly_stats
    
    else:  # month
        # Monthly stats
        monthly_stats = {}
        for booking in bookings:
            month_key = booking.parking_timestamp.strftime('%Y-%m')
            if month_key not in monthly_stats:
                monthly_stats[month_key] = {
                    'bookings': 0,
                    'revenue': 0,
                    'completed': 0,
                    'cancelled': 0
                }
            monthly_stats[month_key]['bookings'] += 1
            monthly_stats[month_key]['revenue'] += booking.total_cost or 0
            if booking.booking_status == 'completed':
                monthly_stats[month_key]['completed'] += 1
            elif booking.booking_status == 'cancelled':
                monthly_stats[month_key]['cancelled'] += 1
        
        stats['trends']['monthly'] = monthly_stats
    
    # Additional statistics
    if lot_id:
        # Get occupancy statistics for the specified lot
        lot = ParkingLot.query.get(lot_id)
        if lot:
            total_spots = lot.total_spots
            available_spots = lot.available_spots
            occupancy_rate = ((total_spots - available_spots) / total_spots * 100) if total_spots > 0 else 0
            
            stats['lot_stats'] = {
                'lot_id': lot.id,
                'lot_name': lot.name,
                'total_spots': total_spots,
                'available_spots': available_spots,
                'occupied_spots': total_spots - available_spots,
                'occupancy_rate': round(occupancy_rate, 2)
            }
    
    return jsonify(stats)

@admin_bp.route('/api/parking_lots', methods=['GET'])
@login_required
@admin_required
def api_parking_lots():
    """API endpoint for getting parking lot information."""
    
    # Get all parking lots
    parking_lots = ParkingLot.query.all()
    
    result = []
    for lot in parking_lots:
        # Count spots by type
        standard_spots = ParkingSpot.query.filter_by(lot_id=lot.id, spot_type='standard').count()
        disabled_spots = ParkingSpot.query.filter_by(lot_id=lot.id, spot_type='disabled').count()
        electric_spots = ParkingSpot.query.filter_by(lot_id=lot.id, spot_type='electric').count()
        
        # Count available spots
        available_spots = ParkingSpot.query.filter_by(lot_id=lot.id, is_available=True).count()
        
        lot_data = {
            'id': lot.id,
            'name': lot.name,
            'address': lot.address,
            'pin_code': lot.pin_code,
            'total_spots': lot.total_spots,
            'available_spots': available_spots,
            'occupied_spots': lot.total_spots - available_spots,
            'occupancy_rate': round(((lot.total_spots - available_spots) / lot.total_spots * 100) 
                                   if lot.total_spots > 0 else 0, 2),
            'price': lot.price,
            'spot_types': {
                'standard': standard_spots,
                'disabled': disabled_spots,
                'electric': electric_spots
            }
        }
        result.append(lot_data)
    
    return jsonify({
        'status': 'success',
        'count': len(result),
        'data': result
    })