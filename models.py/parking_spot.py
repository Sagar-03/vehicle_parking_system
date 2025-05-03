from models import db

class ParkingSpot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lot_id = db.Column(db.Integer, db.ForeignKey('parking_lot.id'), nullable=False)
    status = db.Column(db.String(1), default='A')  # A = Available, O = Occupied

    bookings = db.relationship('Booking', backref='spot', lazy=True)
