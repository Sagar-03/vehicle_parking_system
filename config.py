import os

class Config:
    SECRET_KEY = 'your-secret-key'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///vehicle_parking.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
