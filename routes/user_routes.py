from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, login_user, logout_user, current_user
from extensions import db
from models.user import User
from models.parking_lot import ParkingLot
from models.parking_spot import ParkingSpot
from models.booking import Booking
from models.vehicle import Vehicle
from datetime import datetime, timezone
from functools import wraps
# Using Flask-WTF for CSRF protection and Flask integration
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, HiddenField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length

user_bp = Blueprint('user', __name__, url_prefix='/user')

# Form classes
class RegistrationForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone', validators=[DataRequired()])
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    terms = BooleanField('I agree to the Terms', validators=[DataRequired()])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    email = StringField('Email/Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class VehicleForm(FlaskForm):
    model = StringField('Vehicle Model', validators=[DataRequired(), Length(min=2, max=100)])
    license_plate = StringField('License Plate', validators=[DataRequired(), Length(min=2, max=20)])
    vehicle_type = SelectField('Vehicle Type', choices=[
        ('standard', 'Standard'), 
        ('compact', 'Compact'),
        ('suv', 'SUV'),
        ('electric', 'Electric Vehicle')
    ], validators=[DataRequired()])
    color = StringField('Color', validators=[Length(max=20)])
    submit = SubmitField('Add Vehicle')

class BookingForm(FlaskForm):
    parking_lot_id = SelectField('Parking Lot', coerce=int, validators=[DataRequired()])
    vehicle_id = SelectField('Vehicle', coerce=int)
    duration = StringField('Duration (hours)', validators=[DataRequired()])
    entry_time = StringField('Entry Time', validators=[DataRequired()])
    submit = SubmitField('Find Available Spots')

class ConfirmBookingForm(FlaskForm):
    spot_id = HiddenField('Spot ID', validators=[DataRequired()])
    submit = SubmitField('Confirm Booking')

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
    form = RegistrationForm()
    if form.validate_on_submit():
        # Check if username or email already exists
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already exists!', 'danger')
            return render_template('shared/register.html', form=form)
        
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already registered!', 'danger')
            return render_template('shared/register.html', form=form)
        
        # Create new user
        new_user = User(
            username=form.username.data,
            email=form.email.data,
            password=form.password.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            phone=form.phone.data
        )
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('user.login'))
    
    return render_template('shared/register.html', form=form)

# User login
@user_bp.route('/login', methods=['GET', 'POST'])
def login():
    # Clear any existing sessions first to ensure fresh login
    logout_user()
    
    form = LoginForm()
    if form.validate_on_submit():
        # Check if input is email or username
        user = User.query.filter((User.email == form.email.data) | 
                               (User.username == form.email.data)).first()
        
        if user and user.verify_password(form.password.data):
            login_user(user, remember=form.remember.data)
            flash('Login successful!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('user.dashboard'))
        else:
            flash('Invalid username/email or password.', 'danger')
    
    return render_template('shared/login.html', form=form)

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
    # Get current active booking if any
    active_booking = Booking.query.filter_by(
        user_id=current_user.id, 
        leaving_timestamp=None
    ).first()
    
    # Get past bookings for this user
    past_bookings = Booking.query.filter(
        Booking.user_id == current_user.id,
        Booking.leaving_timestamp.isnot(None)
    ).order_by(Booking.leaving_timestamp.desc()).limit(5).all()
    
    # Calculate total bookings, spent, average duration and preferred location
    total_bookings = Booking.query.filter_by(user_id=current_user.id).count()
    
    # Get all completed bookings
    completed_bookings = Booking.query.filter(
        Booking.user_id == current_user.id,
        Booking.total_cost.isnot(None)
    ).all()
    
    total_spent = sum(booking.total_cost or 0 for booking in completed_bookings)
    
    # Calculate average duration in hours
    if completed_bookings:
        total_hours = sum((booking.leaving_timestamp - booking.parking_timestamp).total_seconds() / 3600 
                         for booking in completed_bookings if booking.leaving_timestamp)
        average_duration = f"{total_hours / len(completed_bookings):.1f} hours" if completed_bookings else "0 hours"
    else:
        average_duration = "0 hours"
    
    # Find the most used parking lot
    lot_usage = {}
    for booking in completed_bookings:
        spot = ParkingSpot.query.get(booking.parking_spot_id)
        if spot:
            lot_id = spot.lot_id
            lot_usage[lot_id] = lot_usage.get(lot_id, 0) + 1
    
    preferred_location = "None"
    if lot_usage:
        max_used_lot_id = max(lot_usage, key=lot_usage.get, default=None)
        if max_used_lot_id:
            lot = ParkingLot.query.get(max_used_lot_id)
            if lot:
                preferred_location = lot.name
    
    # Calculate current fee for active booking
    current_fee = 0
    if active_booking:
        spot = ParkingSpot.query.get(active_booking.parking_spot_id)
        if spot:
            lot = ParkingLot.query.get(spot.lot_id)
            if lot:
                duration = (datetime.now(timezone.utc) - active_booking.parking_timestamp).total_seconds() / 3600
                current_fee = round(duration * lot.price, 2)
    
    # Get user's vehicles
    vehicles = Vehicle.query.filter_by(user_id=current_user.id).all()
    
    # Get available parking lots
    parking_lots = ParkingLot.query.all()
    
    # Create a booking form for the Book Parking tab
    form = BookingForm()
    
    # Get all user's bookings for history tab
    all_bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.parking_timestamp.desc()).all()
    
    # Prepare chart data (last 6 months)
    chart_labels = []
    chart_data = []
    current_date = datetime.now(timezone.utc)
    for i in range(6):
        month_start = current_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if i > 0:
            if month_start.month == 1:
                month_start = month_start.replace(year=month_start.year - 1, month=12)
            else:
                month_start = month_start.replace(month=month_start.month - 1)
        
        month_end = month_start
        if month_start.month == 12:
            month_end = month_start.replace(year=month_start.year + 1, month=1)
        else:
            month_end = month_start.replace(month=month_start.month + 1)
        
        monthly_bookings = Booking.query.filter(
            Booking.user_id == current_user.id,
            Booking.parking_timestamp >= month_start,
            Booking.parking_timestamp < month_end
        ).count()
        
        chart_labels.insert(0, month_start.strftime('%b %Y'))
        chart_data.insert(0, monthly_bookings)
        current_date = month_start
    
    return render_template('user/user_dashboard.html', 
                          current_booking=active_booking,
                          bookings=all_bookings,
                          vehicles=vehicles,
                          parking_lots=parking_lots,
                          form=form,
                          total_bookings=total_bookings,
                          total_spent=round(total_spent, 2),
                          average_duration=average_duration,
                          preferred_location=preferred_location,
                          current_fee=current_fee,
                          chart_labels=chart_labels,
                          chart_data=chart_data)

# Book a parking spot
@user_bp.route('/book_parking', methods=['GET', 'POST'])
@login_required
@user_required
def book_parking():
    form = BookingForm()
    confirmation_form = ConfirmBookingForm()
    
    # Check if user already has an active booking
    active_booking = Booking.query.filter_by(
        user_id=current_user.id, 
        booking_status='active'
    ).first()
    
    if active_booking:
        flash('You already have an active booking. Please release your current spot before booking a new one.', 'warning')
        return redirect(url_for('user.dashboard'))
    
    # Get all parking lots for the dropdown
    parking_lots = ParkingLot.query.all()
    form.parking_lot_id.choices = [(lot.id, f"{lot.name} ({lot.available_spots} spots available)") for lot in parking_lots]
    
    # Get user's vehicles for the dropdown
    user_vehicles = Vehicle.query.filter_by(user_id=current_user.id).all()
    
    if not user_vehicles:
        flash('You need to add a vehicle before booking a parking spot.', 'warning')
        return redirect(url_for('user.vehicles'))
    
    form.vehicle_id.choices = [(v.id, f"{v.model} ({v.license_plate})") for v in user_vehicles]
    
    available_spots = []
    
    if request.method == 'POST' and form.validate():
        lot_id = form.parking_lot_id.data
        
        # Find available spots in the selected lot
        available_spots = ParkingSpot.query.filter_by(
            lot_id=lot_id,
            is_available=True
        ).all()
        
        if not available_spots:
            flash('Sorry, no spots available in the selected parking lot.', 'danger')
    
    # If confirmation form is submitted
    if request.method == 'POST' and confirmation_form.validate():
        spot_id = confirmation_form.spot_id.data
        vehicle_id = form.vehicle_id.data
        spot = ParkingSpot.query.get(spot_id)
        vehicle = Vehicle.query.get(vehicle_id)
        
        if not spot or not spot.is_available:
            flash('Selected parking spot is not available.', 'danger')
            return redirect(url_for('user.book_parking'))
        
        if not vehicle or vehicle.user_id != current_user.id:
            flash('Invalid vehicle selected.', 'danger')
            return redirect(url_for('user.book_parking'))
        
        # Create a new booking
        booking = Booking(
            user_id=current_user.id, 
            parking_spot_id=spot.id,
            vehicle_id=vehicle.id,
            vehicle_reg=vehicle.license_plate  # For backward compatibility
        )
        
        db.session.add(booking)
        db.session.commit()
        
        flash('Parking spot booked successfully!', 'success')
        return redirect(url_for('user.dashboard'))
    
    return render_template('user/book_parking.html', 
                          form=form,
                          confirmation_form=confirmation_form,
                          parking_lots=parking_lots,
                          user_vehicles=user_vehicles,
                          available_spots=available_spots)

# Release parking
@user_bp.route('/release_parking', methods=['GET', 'POST'])
@login_required
@user_required
def release_parking():
    # Get current active booking
    booking = Booking.query.filter_by(
        user_id=current_user.id,
        leaving_timestamp=None
    ).first()
    
    if not booking:
        flash('You do not have any active parking to release.', 'warning')
        return redirect(url_for('user.dashboard'))
    
    if request.method == 'POST':
        # End the booking
        booking.end_booking()
        db.session.commit()
        
        flash(f'Parking spot released successfully. Your total cost was ${booking.total_cost:.2f}', 'success')
        return redirect(url_for('user.dashboard'))
    
    # Get spot and lot info
    spot = ParkingSpot.query.get(booking.parking_spot_id)
    lot = None
    if spot:
        lot = ParkingLot.query.get(spot.lot_id)
    
    # Calculate current duration and cost
    current_duration = (datetime.now(timezone.utc) - booking.parking_timestamp).total_seconds() / 3600
    current_cost = 0
    if lot:
        current_cost = current_duration * lot.price
    
    return render_template('user/release_parking.html', 
                          booking=booking,
                          spot=spot,
                          lot=lot,
                          current_duration=current_duration,
                          current_cost=current_cost)

# View parking history
@user_bp.route('/history')
@login_required
@user_required
def history():
    # Get all past bookings
    bookings = Booking.query.filter(
        Booking.user_id == current_user.id,
        Booking.leaving_timestamp.isnot(None)
    ).order_by(Booking.leaving_timestamp.desc()).all()
    
    return render_template('user/history.html', bookings=bookings)

# View parking summary
@user_bp.route('/summary')
@login_required
@user_required
def summary():
    # Get all completed bookings
    completed_bookings = Booking.query.filter(
        Booking.user_id == current_user.id,
        Booking.leaving_timestamp.isnot(None)
    ).all()
    
    # Calculate total bookings, hours, and spending
    total_bookings = len(completed_bookings)
    total_hours = sum((booking.leaving_timestamp - booking.parking_timestamp).total_seconds() / 3600 
                     for booking in completed_bookings)
    total_spent = sum(booking.total_cost or 0 for booking in completed_bookings)
    avg_duration = total_hours / total_bookings if total_bookings > 0 else 0
    
    # Generate data for charts
    parking_data = {}
    for booking in completed_bookings:
        date_key = booking.parking_timestamp.strftime('%Y-%m-%d')
        if date_key not in parking_data:
            parking_data[date_key] = {'hours': 0, 'cost': 0}
        
        hours = (booking.leaving_timestamp - booking.parking_timestamp).total_seconds() / 3600
        parking_data[date_key]['hours'] += hours
        parking_data[date_key]['cost'] += booking.total_cost or 0
    
    # Get area usage statistics
    area_usage = {}
    for booking in completed_bookings:
        spot = ParkingSpot.query.get(booking.parking_spot_id)
        if spot:
            lot = ParkingLot.query.get(spot.lot_id)
            if lot:
                area_key = lot.name
                if area_key not in area_usage:
                    area_usage[area_key] = 0
                area_usage[area_key] += 1
    
    return render_template('user/summary.html',
                          total_bookings=total_bookings,
                          total_hours=round(total_hours, 1),
                          total_spent=round(total_spent, 2),
                          avg_duration=round(avg_duration, 1),
                          parking_data=parking_data,
                          area_usage=area_usage)

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

# Vehicle management
@user_bp.route('/vehicles', methods=['GET', 'POST'])
@login_required
@user_required
def vehicles():
    form = VehicleForm()
    
    # Get user's vehicles
    user_vehicles = Vehicle.query.filter_by(user_id=current_user.id).all()
    
    if request.method == 'POST' and form.validate():
        # Check if license plate already exists
        existing_vehicle = Vehicle.query.filter_by(license_plate=form.license_plate.data).first()
        if existing_vehicle:
            flash('A vehicle with this license plate already exists.', 'danger')
            return redirect(url_for('user.vehicles'))
        
        # Create new vehicle
        vehicle = Vehicle(
            user_id=current_user.id,
            model=form.model.data,
            license_plate=form.license_plate.data,
            vehicle_type=form.vehicle_type.data,
            color=form.color.data
        )
        
        db.session.add(vehicle)
        db.session.commit()
        
        flash('Vehicle added successfully!', 'success')
        return redirect(url_for('user.vehicles'))
    
    return render_template('user/vehicles.html', form=form, vehicles=user_vehicles)

@user_bp.route('/delete_vehicle/<int:vehicle_id>', methods=['POST'])
@login_required
@user_required
def delete_vehicle(vehicle_id):
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    
    # Check if this vehicle belongs to the current user
    if vehicle.user_id != current_user.id:
        flash('You do not have permission to delete this vehicle.', 'danger')
        return redirect(url_for('user.vehicles'))
    
    # Check if vehicle is currently being used in an active booking
    active_booking = Booking.query.filter_by(vehicle_id=vehicle_id, booking_status='active').first()
    if active_booking:
        flash('Cannot delete a vehicle that is currently being used in an active booking.', 'danger')
        return redirect(url_for('user.vehicles'))
    
    # Delete the vehicle
    db.session.delete(vehicle)
    db.session.commit()
    
    flash('Vehicle deleted successfully!', 'success')
    return redirect(url_for('user.vehicles'))

# Search parking lots
@user_bp.route('/search_parking')
@login_required
@user_required
def search_parking():
    # Get search parameters
    search_term = request.args.get('search', '')
    search_type = request.args.get('type', 'area')  # 'area' or 'pincode'
    
    # Perform search
    if search_term:
        if search_type == 'pincode':
            parking_lots = ParkingLot.query.filter(ParkingLot.pin_code.ilike(f'%{search_term}%')).all()
        else:  # default to area search
            parking_lots = ParkingLot.query.filter(ParkingLot.name.ilike(f'%{search_term}%') | 
                                                 ParkingLot.address.ilike(f'%{search_term}%')).all()
    else:
        # If no search term, return all lots
        parking_lots = ParkingLot.query.all()
    
    return render_template('user/search_parking.html', 
                          parking_lots=parking_lots,
                          search_term=search_term,
                          search_type=search_type)