from models import db

class ParkingLot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    prime_location_name = db.Column(db.String(100))
    address = db.Column(db.String(200))
    pin_code = db.Column(db.String(10))
    price = db.Column(db.Float)
    max_spots = db.Column(db.Integer)

    spots = db.relationship('ParkingSpot', backref='lot', cascade="all, delete", lazy=True)
