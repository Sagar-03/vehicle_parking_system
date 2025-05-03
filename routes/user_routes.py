from flask import render_template, request, redirect, url_for, flash, session
from routes import user_bp
from models.parking_lot import ParkingLot
from models.parking_spot import ParkingSpot
from models.booking import Booking
from models.user import User
from utils.db import db
from datetime import datetime

@user_bp.route('/')
def home():
    lots = ParkingLot.query.all()
    return render_template('user/home.html', lots=lots)

@user_bp.route('/book/<int:spot_id>', methods=['GET', 'POST'])
def book_spot(spot_id):
    spot = ParkingSpot.query.get_or_404(spot_id)
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        vehicle_number = request.form['vehicle_number']
        user = User(name=name, email=email, vehicle_number=vehicle_number)
        db.session.add(user)
        db.session.commit()

        booking = Booking(user_id=user.id, spot_id=spot.id, booked_on=datetime.now())
        db.session.add(booking)
        spot.is_available = False
        db.session.commit()
        flash('Booking confirmed!')
        return redirect(url_for('user.view_booking', booking_id=booking.id))

    return render_template('user/book.html', spot=spot)

@user_bp.route('/booking/<int:booking_id>')
def view_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    return render_template('user/booking_detail.html', booking=booking)
