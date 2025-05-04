from extensions import db
from datetime import datetime

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    parking_spot_id = db.Column(db.Integer, db.ForeignKey('parking_spot.id'), nullable=False)
    vehicle_reg = db.Column(db.String(20), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    booking_status = db.Column(db.String(20), default='active')  # active, completed, cancelled
    created_on = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, user_id, parking_spot_id, vehicle_reg, start_time, end_time, booking_status='active'):
        self.user_id = user_id
        self.parking_spot_id = parking_spot_id
        self.vehicle_reg = vehicle_reg
        self.start_time = start_time
        self.end_time = end_time
        self.booking_status = booking_status
        
        # Update the parking spot availability
        from models.parking_spot import ParkingSpot
        spot = ParkingSpot.query.get(parking_spot_id)
        if spot:
            spot.update_availability(False)
    
    def cancel_booking(self):
        """Cancel this booking and update the parking spot availability"""
        self.booking_status = 'cancelled'
        db.session.commit()
        
        # Update the parking spot availability
        from models.parking_spot import ParkingSpot
        spot = ParkingSpot.query.get(self.parking_spot_id)
        if spot:
            spot.update_availability(True)
    
    def complete_booking(self):
        """Mark the booking as completed and update the parking spot availability"""
        self.booking_status = 'completed'
        db.session.commit()
        
        # Update the parking spot availability
        from models.parking_spot import ParkingSpot
        spot = ParkingSpot.query.get(self.parking_spot_id)
        if spot:
            spot.update_availability(True)
    
    def __repr__(self):
        return f'<Booking {self.id} for User {self.user_id}>'