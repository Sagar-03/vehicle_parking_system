from extensions import db
from datetime import datetime

class ParkingSpot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    spot_id = db.Column(db.String(50), nullable=False)
    parking_lot_id = db.Column(db.Integer, db.ForeignKey('parking_lot.id'), nullable=False)
    is_available = db.Column(db.Boolean, default=True)
    spot_type = db.Column(db.String(50), default='standard')  # standard, disabled, electric, etc.
    created_on = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    bookings = db.relationship('Booking', backref='parking_spot', lazy=True, cascade="all, delete-orphan")
    
    def __init__(self, spot_id, parking_lot_id, spot_type='standard', is_available=True):
        self.spot_id = spot_id
        self.parking_lot_id = parking_lot_id
        self.spot_type = spot_type
        self.is_available = is_available
    
    def update_availability(self, is_available):
        """Update the availability of this parking spot"""
        self.is_available = is_available
        db.session.commit()
        
        # Update parent parking lot's available spots count
        from models.parking_lot import ParkingLot
        parking_lot = ParkingLot.query.get(self.parking_lot_id)
        if parking_lot:
            parking_lot.update_available_spots()
    
    def __repr__(self):
        return f'<ParkingSpot {self.spot_id} at Lot {self.parking_lot_id}>'