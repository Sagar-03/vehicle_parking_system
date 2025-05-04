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
    
    # Virtual attributes (not in the database)
    _price = 2.50  # Default price
    _total_spots = 0  # Default total spots
    
    # Relationships
    parking_spots = db.relationship('ParkingSpot', backref='parking_lot', lazy=True, cascade="all, delete-orphan")
    
    def __init__(self, name, address, pin_code, price=2.50, available_spots=0, total_spots=0, postcode_level=None):
        self.name = name
        self.address = address
        self.pin_code = pin_code
        self.postcode_level = postcode_level
        self._price = price  # Store as instance attribute (not in DB)
        self.available_spots = available_spots
        self._total_spots = total_spots  # Store as instance attribute (not in DB)
    
    @property
    def price(self):
        """Virtual attribute for price/hourly rate"""
        return self._price
    
    @price.setter
    def price(self, value):
        self._price = value
    
    @property
    def hourly_rate(self):
        """Alias for price"""
        return self._price
        
    @hourly_rate.setter
    def hourly_rate(self, value):
        self._price = value
    
    @property
    def total_spots(self):
        """Virtual attribute for total spots"""
        return self._total_spots
    
    @total_spots.setter
    def total_spots(self, value):
        self._total_spots = value
    
    @property
    def maximum_spots(self):
        """Alias for total_spots"""
        return self._total_spots
    
    @maximum_spots.setter
    def maximum_spots(self, value):
        self._total_spots = value
    
    @property
    def prime_location_name(self):
        """Alias for name"""
        return self.name
    
    @prime_location_name.setter
    def prime_location_name(self, value):
        self.name = value
    
    def update_available_spots(self):
        """Update the count of available spots based on associated ParkingSpot objects"""
        from models.parking_spot import ParkingSpot
        available = ParkingSpot.query.filter_by(lot_id=self.id, is_available=True).count()
        self.available_spots = available
        db.session.commit()
    
    def available_spots_count(self):
        """Get the current count of available spots"""
        return self.available_spots
    
    def occupied_spots_count(self):
        """Get the current count of occupied spots"""
        from models.parking_spot import ParkingSpot
        return ParkingSpot.query.filter_by(lot_id=self.id, is_available=False).count()
    
    def __repr__(self):
        return f'<ParkingLot {self.name}>'