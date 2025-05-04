from extensions import db
from datetime import datetime

class Vehicle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    model = db.Column(db.String(100), nullable=False)
    license_plate = db.Column(db.String(20), nullable=False, unique=True)
    vehicle_type = db.Column(db.String(20), default='standard')  # standard, compact, SUV, electric, etc.
    color = db.Column(db.String(20))
    created_on = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    bookings = db.relationship('Booking', backref='vehicle', lazy=True)
    
    def __init__(self, user_id, model, license_plate, vehicle_type='standard', color=None):
        self.user_id = user_id
        self.model = model
        self.license_plate = license_plate
        self.vehicle_type = vehicle_type
        self.color = color
    
    def __repr__(self):
        return f'<Vehicle {self.license_plate}>'