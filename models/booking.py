from extensions import db
from datetime import datetime, timezone

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    parking_spot_id = db.Column(db.Integer, db.ForeignKey('parking_spot.id'), nullable=False)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicle.id'), nullable=True)  # Added foreign key to vehicle
    vehicle_reg = db.Column(db.String(20), nullable=True)  # Kept for backward compatibility
    parking_timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    leaving_timestamp = db.Column(db.DateTime, nullable=True)
    total_cost = db.Column(db.Float, nullable=True)
    booking_status = db.Column(db.String(20), default='active')  # active, completed, cancelled
    created_on = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Keeping these for compatibility
    start_time = db.Column(db.DateTime, nullable=True)
    end_time = db.Column(db.DateTime, nullable=True)
    
    def __init__(self, user_id, parking_spot_id, vehicle_id=None, vehicle_reg=None, booking_status='active'):
        self.user_id = user_id
        self.parking_spot_id = parking_spot_id
        self.vehicle_id = vehicle_id
        self.vehicle_reg = vehicle_reg
        self.booking_status = booking_status
        self.parking_timestamp = datetime.now(timezone.utc)
        
        # Update the parking spot availability
        from models.parking_spot import ParkingSpot
        spot = ParkingSpot.query.get(parking_spot_id)
        if spot:
            spot.is_available = False
            db.session.add(spot)
    
    def cancel_booking(self):
        """Cancel this booking and update the parking spot availability"""
        self.booking_status = 'cancelled'
        
        # Update the parking spot availability
        from models.parking_spot import ParkingSpot
        spot = ParkingSpot.query.get(self.parking_spot_id)
        if spot:
            spot.is_available = True
            db.session.add(spot)
    
    def end_booking(self):
        """End this booking, calculate cost and mark the spot as available"""
        self.leaving_timestamp = datetime.now(timezone.utc)
        self.booking_status = 'completed'
        
        # Calculate duration in hours
        duration = (self.leaving_timestamp - self.parking_timestamp).total_seconds() / 3600
        
        # Get parking rate from the lot
        from models.parking_spot import ParkingSpot
        from models.parking_lot import ParkingLot
        
        spot = ParkingSpot.query.get(self.parking_spot_id)
        if spot:
            lot = ParkingLot.query.get(spot.parking_lot_id)
            if lot and hasattr(lot, 'price'):
                hourly_rate = lot.price
                self.total_cost = round(duration * hourly_rate, 2)
            else:
                # Default rate if lot price not available
                self.total_cost = round(duration * 2.50, 2)
            
            # Mark spot as available
            spot.is_available = True
            db.session.add(spot)
    
    def __repr__(self):
        return f'<Booking {self.id} for User {self.user_id}>'