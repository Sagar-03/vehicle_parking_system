from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Import all models to register them with SQLAlchemy
from models.user import User
from models.admin import Admin
from models.parking_lot import ParkingLot
from models.parking_spot import ParkingSpot
from models.booking import Booking
