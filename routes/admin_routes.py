from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, login_user, logout_user, current_user
from app import db
from models.admin import Admin
from models.user import User
from models.parking_lot import ParkingLot
from models.parking_spot import ParkingSpot
from models.booking import Booking
from functools import wraps

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Custom decorator to check if the user is an admin
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not isinstance(current_user, Admin):
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function

# Admin login
@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        admin = Admin.query.filter_by(username=username).first()
        
        if admin and admin.verify_password(password):
            login_user(admin)
            flash('Login successful!', 'success')
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Invalid username or password.', 'danger')
    
    return render_template('admin/login.html')

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
    total_lots = ParkingLot.query.count()
    total_spots = ParkingSpot.query.count()
    available_spots = ParkingSpot.query.filter_by(status='A').count()
    occupied_spots = ParkingSpot.query.filter_by(status='O').count()
    total_users = User.query.count()
    total_bookings = Booking.query.count()
    
    return render_template('admin/dashboard.html', 
                           total_lots=total_lots,
                           total_spots=total_spots,
                           available_spots=available_spots,
                           occupied_spots=occupied_spots,
                           total_users=total_users,
                           total_bookings=total_bookings)

# Manage parking lots
@admin_bp.route('/lots')
@login_required
@admin_required
def manage_lots():
    lots = ParkingLot.query.all()
    return render_template('admin/manage_lots.html', lots=lots)

# Add new parking lot
@admin_bp.route('/lots/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_lot():
    if request.method == 'POST':
        location_name = request.form.get('location_name')
        price = float(request.form.get('price'))
        address = request.form.get('address')
        pin_code = request.form.get('pin_code')
        max_spots = int(request.form.get('max_spots'))
        
        new_lot = ParkingLot(
            prime_location_name=location_name,
            price=price,
            address=address,
            pin_code=pin_code,
            maximum_spots=max_spots
        )
        
        db.session.add(new_lot)
        db.session.commit()
        
        # Create parking spots for this lot
        for i in range(1, max_spots + 1):
            spot = ParkingSpot(lot_id=new_lot.id, spot_number=i)
            db.session.add(spot)
        
        db.session.commit()
        flash(f'Parking lot "{location_name}" created successfully with {max_spots} spots.', 'success')
        return redirect(url_for('admin.manage_lots'))
    
    return render_template('admin/add_lot.html')

# Edit parking lot
@admin_bp.route('/lots/edit/<int:lot_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_lot(lot_id):
    lot = ParkingLot.query.get_or_404(lot_id)
    
    if request.method == 'POST':
        lot.prime_location_name = request.form.get('location_name')
        lot.price = float(request.form.get('price'))
        lot.address = request.form.get('address')
        lot.pin_code = request.form.get('pin_code')
        new_max_spots = int(request.form.get('max_spots'))
        
        current_spots_count = lot.spots.count()
        
        # If increasing spots, add new ones
        if new_max_spots > current_spots_count:
            for i in range(current_spots_count + 1, new_max_spots + 1):
                spot = ParkingSpot(lot_id=lot.id, spot_number=i)
                db.session.add(spot)
        
        # If decreasing spots, remove unoccupied ones from the end
        elif new_max_spots < current_spots_count:
            # Check if any of the spots to be removed are occupied
            for i in range(new_max_spots + 1, current_spots_count + 1):
                spot = ParkingSpot.query.filter_by(lot_id=lot.id, spot_number=i).first()
                if spot and spot.status == 'O':
                    flash(f'Cannot reduce spots. Spot {i} is currently occupied.', 'danger')
                    return redirect(url_for('admin.edit_lot', lot_id=lot_id))
            
            # Safe to remove spots
            for i in range(new_max_spots + 1, current_spots_count + 1):
                spot = ParkingSpot.query.filter_by(lot_id=lot.id, spot_number=i).first()
                if spot:
                    db.session.delete(spot)
        
        lot.maximum_spots = new_max_spots
        db.session.commit()
        flash(f'Parking lot "{lot.prime_location_name}" updated successfully.', 'success')
        return redirect(url_for('admin.manage_lots'))
    
    return render_template('admin/edit_lot.html', lot=lot)

# Delete parking lot
@admin_bp.route('/lots/delete/<int:lot_id>', methods=['POST'])
@login_required
@admin_required
def delete_lot(lot_id):
    lot = ParkingLot.query.get_or_404(lot_id)
    
    # Check if any spots in this lot are occupied
    occupied_spots = ParkingSpot.query.filter_by(lot_id=lot_id, status='O').count()
    if occupied_spots > 0:
        flash(f'Cannot delete parking lot. {occupied_spots} spots are currently occupied.', 'danger')
        return redirect(url_for('admin.manage_lots'))
    
    # It's safe to delete
    db.session.delete(lot)
    db.session.commit()
    flash(f'Parking lot "{lot.prime_location_name}" deleted successfully.', 'success')
    return redirect(url_for('admin.manage_lots'))

# Manage parking spots
@admin_bp.route('/spots')
@login_required
@admin_required
def manage_spots():
    lots = ParkingLot.query.all()
    selected_lot_id = request.args.get('lot_id', type=int)
    
    if selected_lot_id:
        spots = ParkingSpot.query.filter_by(lot_id=selected_lot_id).order_by(ParkingSpot.spot_number).all()
        selected_lot = ParkingLot.query.get(selected_lot_id)
    else:
        spots = []
        selected_lot = None
    
    return render_template('admin/manage_spots.html', 
                          lots=lots, 
                          selected_lot=selected_lot,
                          spots=spots)

# View spot details
@admin_bp.route('/spots/<int:spot_id>')
@login_required
@admin_required
def spot_details(spot_id):
    spot = ParkingSpot.query.get_or_404(spot_id)
    current_booking = spot.current_booking()
    
    return render_template('admin/spot_details.html', spot=spot, booking=current_booking)

# Manage users
@admin_bp.route('/users')
@login_required
@admin_required
def manage_users():
    users = User.query.all()
    return render_template('admin/users_list.html', users=users)

# View user bookings
@admin_bp.route('/users/<int:user_id>/bookings')
@login_required
@admin_required
def user_bookings(user_id):
    user = User.query.get_or_404(user_id)
    bookings = Booking.query.filter_by(user_id=user_id).order_by(Booking.parking_timestamp.desc()).all()
    
    return render_template('admin/user_bookings.html', user=user, bookings=bookings)

# API endpoints for charts
@admin_bp.route('/api/lot_stats')
@login_required
@admin_required
def lot_stats():
    lots = ParkingLot.query.all()
    stats = []
    
    for lot in lots:
        stats.append({
            'name': lot.prime_location_name,
            'total': lot.maximum_spots,
            'available': lot.available_spots_count(),
            'occupied': lot.occupied_spots_count()
        })
    
    return jsonify(stats)