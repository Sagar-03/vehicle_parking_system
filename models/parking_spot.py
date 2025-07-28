from extensions import db
from datetime import datetime, timezone, timezone


class ParkingSpot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    spot_id = db.Column(db.String(50), nullable=False, unique=True)
    spot_number = db.Column(db.Integer, nullable=False)  # New: store the spot number as integer
    parking_lot_id = db.Column(db.Integer, db.ForeignKey('parking_lot.id'), nullable=False)
    is_available = db.Column(db.Boolean, default=True)
    spot_type = db.Column(db.String(50), default='standard')  # standard, disabled, electric, etc.
    created_on = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    bookings = db.relationship('Booking', backref='spot', lazy=True, cascade="all, delete-orphan")

    def __init__(self, lot_id, spot_number, spot_type='standard', is_available=True):
        self.parking_lot_id = lot_id
        self.spot_number = spot_number
        self.spot_type = spot_type
        self.is_available = is_available
        self.spot_id = f"L{lot_id}-S{spot_number}"

    @property
    def status(self):
        return 'A' if self.is_available else 'O'

    def mark_occupied(self):
        self.is_available = False

    def mark_available(self):
        self.is_available = True
    
    # Compatibility property for lot_id
    @property
    def lot_id(self):
        return self.parking_lot_id
    @lot_id.setter
    def lot_id(self, value):
        self.parking_lot_id = value
    
    def update_availability(self, is_available):
        """Update the availability of this parking spot and parent lot's available count."""
        self.is_available = is_available
        from models.parking_lot import ParkingLot
        parking_lot = ParkingLot.query.get(self.parking_lot_id)
        if parking_lot:
            if is_available:
                parking_lot.available_spots = min(parking_lot.available_spots + 1, len(parking_lot.parking_spots))
            else:
                parking_lot.available_spots = max(0, parking_lot.available_spots - 1)
            db.session.add(parking_lot)
    
    def current_booking(self):
        """Get the current active booking for this spot if any. Returns None if no active booking exists."""
        from models.booking import Booking
        booking = Booking.query.filter_by(
            parking_spot_id=self.id,
            booking_status='active'
        ).first()
        return booking if booking else None
    
    def __repr__(self):
        return f'<ParkingSpot {self.spot_id} at Lot {self.parking_lot_id}>'