from extensions import db
from datetime import datetime, timezone, timezone

class ParkingSpot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    spot_id = db.Column(db.String(50), nullable=False)
    parking_lot_id = db.Column(db.Integer, db.ForeignKey('parking_lot.id'), nullable=False)
    is_available = db.Column(db.Boolean, default=True)
    spot_type = db.Column(db.String(50), default='standard')  # standard, disabled, electric, etc.
    created_on = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Virtual attributes (not in the database)
    _spot_number = 0
    _status = 'A'
    
    # Relationships
    bookings = db.relationship('Booking', backref='spot', lazy=True, cascade="all, delete-orphan")
    
    def __init__(self, lot_id, spot_number, spot_type='standard', is_available=True):
        self.parking_lot_id = lot_id
        self._spot_number = spot_number
        self.spot_type = spot_type
        self.is_available = is_available
        self._status = 'A' if is_available else 'O'
        
        # Generate a spot_id based on lot and spot number
        # This will be something like A-1, A-2, etc.
        self.spot_id = f"{chr(64 + (lot_id % 26) + 1)}-{spot_number}"
    
    # Compatibility properties
    @property
    def lot_id(self):
        return self.parking_lot_id
    
    @lot_id.setter
    def lot_id(self, value):
        self.parking_lot_id = value
    
    @property
    def spot_number(self):
        return self._spot_number
    
    @spot_number.setter
    def spot_number(self, value):
        self._spot_number = value
        # Update spot_id whenever spot_number changes
        if hasattr(self, 'parking_lot_id'):
            self.spot_id = f"{chr(64 + (self.parking_lot_id % 26) + 1)}-{value}"
    
    @property
    def status(self):
        return 'A' if self.is_available else 'O'
    
    @status.setter
    def status(self, value):
        if value == 'A':
            self.is_available = True
        elif value == 'O' or value == 'M':
            self.is_available = False
    
    def update_availability(self, is_available):
        """Update the availability of this parking spot"""
        self.is_available = is_available
        self._status = 'A' if is_available else 'O'
        db.session.commit()
        
        # Update parent parking lot's available spots count
        from models.parking_lot import ParkingLot
        parking_lot = ParkingLot.query.get(self.parking_lot_id)
        if parking_lot:
            parking_lot.update_available_spots()
    
    def current_booking(self):
        """Get the current active booking for this spot if any"""
        from models.booking import Booking
        return Booking.query.filter_by(
            parking_spot_id=self.id, 
            leaving_timestamp=None
        ).first()
    
    def __repr__(self):
        return f'<ParkingSpot {self.spot_id} at Lot {self.parking_lot_id}>'