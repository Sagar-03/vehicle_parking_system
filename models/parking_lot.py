from extensions import db
from datetime import datetime

class ParkingLot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    pin_code = db.Column(db.String(20), nullable=False)
    postcode_level = db.Column(db.String(50))
    available_spots = db.Column(db.Integer, default=0)
    created_on = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    parking_spots = db.relationship('ParkingSpot', backref='parking_lot', lazy=True, cascade="all, delete-orphan")
    
    def __init__(self, name, address, pin_code, postcode_level=None, available_spots=0):
        self.name = name
        self.address = address
        self.pin_code = pin_code
        self.postcode_level = postcode_level
        self.available_spots = available_spots
    
    def update_available_spots(self):
        """Update the count of available spots based on associated ParkingSpot objects"""
        from models.parking_spot import ParkingSpot
        available = ParkingSpot.query.filter_by(parking_lot_id=self.id, is_available=True).count()
        self.available_spots = available
        db.session.commit()
    
    def __repr__(self):
        return f'<ParkingLot {self.name}>'