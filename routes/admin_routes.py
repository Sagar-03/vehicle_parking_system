from flask import render_template, request, redirect, url_for, flash
from routes import admin_bp
from models.admin import Admin
from models.parking_lot import ParkingLot
from models.parking_spot import ParkingSpot
from models.booking import Booking
from models.user import User
from utils.db import db

@admin_bp.route('/admin/dashboard')
def admin_dashboard():
    lots = ParkingLot.query.all()
    return render_template('admin/dashboard.html', lots=lots)

@admin_bp.route('/admin/add_lot', methods=['GET', 'POST'])
def add_parking_lot():
    if request.method == 'POST':
        name = request.form['name']
        location = request.form['location']
        new_lot = ParkingLot(name=name, location=location)
        db.session.add(new_lot)
        db.session.commit()
        flash('Parking lot added successfully.')
        return redirect(url_for('admin.admin_dashboard'))
    return render_template('admin/add_lot.html')

@admin_bp.route('/admin/slots/<int:lot_id>')
def view_slots(lot_id):
    spots = ParkingSpot.query.filter_by(lot_id=lot_id).all()
    return render_template('admin/view_slots.html', spots=spots)

@admin_bp.route('/admin/bookings')
def view_all_bookings():
    bookings = Booking.query.all()
    return render_template('admin/bookings.html', bookings=bookings)
