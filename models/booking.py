from extensions import db
from datetime import datetime, timezone

class Booking(db.Model):
    @property
    def username(self):
        """Return the username of the user who made this booking, or None if not found."""
        if hasattr(self, 'user') and self.user:
            return self.user.username
        # fallback if relationship is not loaded
        from models.user import User
        user = User.query.get(self.user_id)
        return user.username if user else None
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
            # Verify spot is still available before booking
            if not spot.is_available:
                raise ValueError("This parking spot is no longer available")
                
            spot.is_available = False
            db.session.add(spot)
            
            # Also update the parent lot's available spots
            from models.parking_lot import ParkingLot
            lot = ParkingLot.query.get(spot.parking_lot_id)
            if lot:
                lot.available_spots = max(0, lot.available_spots - 1)
                db.session.add(lot)
    
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
        from datetime import datetime, timezone
        self.leaving_timestamp = datetime.now(timezone.utc)
        self.booking_status = 'completed'
        
        # Calculate total cost
        if self.parking_timestamp and self.leaving_timestamp:
            parking_time = self.parking_timestamp
            if parking_time.tzinfo is None or parking_time.tzinfo.utcoffset(parking_time) is None:
                parking_time = parking_time.replace(tzinfo=timezone.utc)
            duration_hours = (self.leaving_timestamp - parking_time).total_seconds() / 3600
        
        # Get parking rate from the lot
        from models.parking_spot import ParkingSpot
        from models.parking_lot import ParkingLot
        
        spot = ParkingSpot.query.get(self.parking_spot_id)
        if spot:
            lot = ParkingLot.query.get(spot.parking_lot_id)
            if lot and hasattr(lot, 'price'):
                self.total_cost = round(duration_hours * lot.price, 2)
            else:
                # Default rate if lot price not available
                self.total_cost = round(duration_hours * 2.50, 2)
            
            # Mark spot as available
            spot.is_available = True
            db.session.add(spot)
            
            # Update the lot's available spots
            if lot:
                lot.available_spots = lot.available_spots + 1
                db.session.add(lot)
    
    def calculate_total_cost(self):
        """Calculate and set the total cost for this booking based on duration and lot price."""
        if not self.parking_timestamp or not self.leaving_timestamp:
            self.total_cost = 0.0
            return
        parking_time = self.parking_timestamp
        leaving_time = self.leaving_timestamp
        # Ensure both are timezone-aware
        from datetime import timezone
        if parking_time.tzinfo is None or parking_time.tzinfo.utcoffset(parking_time) is None:
            parking_time = parking_time.replace(tzinfo=timezone.utc)
        if leaving_time.tzinfo is None or leaving_time.tzinfo.utcoffset(leaving_time) is None:
            leaving_time = leaving_time.replace(tzinfo=timezone.utc)
        duration_hours = (leaving_time - parking_time).total_seconds() / 3600
        from models.parking_spot import ParkingSpot
        from models.parking_lot import ParkingLot
        spot = ParkingSpot.query.get(self.parking_spot_id)
        if spot:
            lot = ParkingLot.query.get(spot.parking_lot_id)
            if lot and hasattr(lot, 'price'):
                self.total_cost = round(duration_hours * lot.price, 2)
            else:
                self.total_cost = round(duration_hours * 2.50, 2)
        else:
            self.total_cost = round(duration_hours * 2.50, 2)

    def __repr__(self):
        return f'<Booking {self.id} for User {self.user_id}>'