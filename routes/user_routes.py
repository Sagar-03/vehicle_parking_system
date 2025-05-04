from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, login_user, logout_user, current_user
from app import db
from models.user import User
from models.parking_lot import ParkingLot
from models.parking_spot import ParkingSpot
from models.booking import Booking
from datetime import datetime
from functools import wraps

user_bp = Blueprint('user', __name__, url_prefix='/user')

# Custom decorator to ensure the user is not an admin
def user_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from models.admin import Admin
        if isinstance(current_user, Admin):
            flash('This feature is only for regular users.', 'danger')
            return redirect(url_for('admin.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# User registration
@user_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        phone = request.form.get('phone')
        
        # Check if passwords match
        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('user.register'))
        
        # Check if username or email already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists!', 'danger')
            return redirect(url_for('user.register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered!', 'danger')
            return redirect(url_for('user.register'))
        
        # Create new user
        new_user = User(username=username, email=email, password=password, phone=phone)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('user.login'))
    
    return render_template('user/register.html')

# User login
@user_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.verify_password(password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('user.dashboard'))
        else:
            flash('Invalid username or password.', 'danger')
    
    return render_template('user/login.html')

# User logout
@user_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('user.login'))

# User dashboard
@user_bp.route('/dashboard')
@login_required
@user_required
def dashboard():
    active_booking = Booking.query.filter_by(
        user_id=current_user.id, 
        leaving_timestamp=None
    ).first()
    
    # Get all completed bookings for the user
    past_bookings = Booking.query.filter(
        Booking.user_id == current_user.id,
        Booking.leaving_timestamp.isnot(None)
    ).order_by(Booking.leaving_timestamp.desc()).limit(5).all()
    
    return render_template('user/dashboard.html', 
                          active_booking=active_booking,
                          past_bookings=past_bookings)

# Book a parking spot
@user_bp.route('/book', methods=['GET', 'POST'])
@login_required
@user_required
def book_spot():
    # Check if user already has an active booking
    active_booking = Booking.query.filter_by(
        user_id=current_user.id, 
        leaving_timestamp=None
    ).first()
    
    if active_booking:
        flash('You already have an active booking. Please release your current spot before booking a new one.', 'warning')
        return redirect(url_for('user.dashboard'))
    
    lots = ParkingLot.query.all()
    
    if request.method == 'POST':
        lot_id = request.form.get('lot_id', type=int)
        
        if not lot_id:
            flash('Please select a parking lot.', 'danger')
            return redirect(url_for('user.book_spot'))
        
        # Find the first available spot in the selected lot
        spot = ParkingSpot.query.filter_by(
            lot_id=lot_id,
            status='A'  # Available
        ).first()
        
        if not spot:
            flash('Sorry, no spots available in the selected parking lot.', 'danger')
            return redirect(url_for('user.book_spot'))
        
        # Create a new booking
        booking = Booking(user_id=current_user.id, spot_id=spot.id)
        
        # Mark the spot as occupied
        spot.status = 'O'  # Occupied
        
        db.session.add(booking)
        db.session.add(spot)
        db.session.commit()
        
        flash('Parking spot booked successfully!', 'success')
        return redirect(url_for('user.dashboard'))
    
    return render_template('user/book_spot.html', lots=lots)

# View active booking details
@user_bp.route('/booking/<int:booking_id>')
@login_required
@user_required
def booking_details(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    
    # Ensure the booking belongs to the current user
    if booking.user_id != current_user.id:
        flash('Access denied. This booking does not belong to you.', 'danger')
        return redirect(url_for('user.dashboard'))
    
    spot = ParkingSpot.query.get(booking.spot_id)
    lot = ParkingLot.query.get(spot.lot_id) if spot else None
    
    # Calculate current duration and cost if booking is active
    current_duration = 0
    current_cost = 0
    
    if not booking.leaving_timestamp:
        # Calculate time difference between now and parking timestamp
        now = datetime.utcnow()
        delta = now - booking.parking_timestamp
        current_duration = delta.total_seconds() / 3600  # Convert to hours
        current_cost = current_duration * lot.price if lot else 0
    
    return render_template('user/booking_details.html',
                          booking=booking,
                          spot=spot,
                          lot=lot,
                          current_duration=current_duration,
                          current_cost=current_cost)

# Release a parking spot
@user_bp.route('/release/<int:booking_id>', methods=['POST'])
@login_required
@user_required
def release_spot(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    
    # Ensure the booking belongs to the current user
    if booking.user_id != current_user.id:
        flash('Access denied. This booking does not belong to you.', 'danger')
        return redirect(url_for('user.dashboard'))
    
    # Ensure the booking is active
    if booking.leaving_timestamp:
        flash('This parking spot has already been released.', 'warning')
        return redirect(url_for('user.dashboard'))
    
    # End the booking (this also updates the spot status to available)
    booking.end_booking()
    
    db.session.add(booking)
    db.session.commit()
    
    flash('Parking spot released successfully. Your total cost was ${:.2f}'.format(booking.total_cost), 'success')
    return redirect(url_for('user.dashboard'))

# View parking history
@user_bp.route('/history')
@login_required
@user_required
def parking_history():
    bookings = Booking.query.filter(
        Booking.user_id == current_user.id,
        Booking.leaving_timestamp.isnot(None)
    ).order_by(Booking.leaving_timestamp.desc()).all()
    
    return render_template('user/parking_history.html', bookings=bookings)

# API endpoint for user parking stats
@user_bp.route('/api/parking_stats')
@login_required
@user_required
def parking_stats():
    # Get user's bookings grouped by month
    bookings = Booking.query.filter(
        Booking.user_id == current_user.id,
        Booking.leaving_timestamp.isnot(None)
    ).order_by(Booking.parking_timestamp).all()
    
    # Prepare data for chart
    months = {}
    for booking in bookings:
        month_key = booking.parking_timestamp.strftime('%Y-%m')
        if month_key not in months:
            months[month_key] = {
                'label': booking.parking_timestamp.strftime('%b %Y'),
                'count': 0,
                'total_cost': 0
            }
        months[month_key]['count'] += 1
        months[month_key]['total_cost'] += booking.total_cost or 0
    
    # Convert to list for JSON response
    stats = [
        {
            'month': data['label'],
            'count': data['count'],
            'total_cost': round(data['total_cost'], 2)
        } for month_key, data in months.items()
    ]
    
    return jsonify(stats)