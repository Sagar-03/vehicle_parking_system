#!/usr/bin/env python3
"""
Script to recreate the database with proper schema
"""

import os
import sqlite3
from app import create_app
from extensions import db

def recreate_database():
    """Drop and recreate the database with current models"""
    
    app = create_app()
    
    with app.app_context():
        # Drop all tables
        print("Dropping all existing tables...")
        db.drop_all()
        
        # Create all tables
        print("Creating all tables with current schema...")
        db.create_all()
        
        # Import models to ensure they're loaded
        from models.admin import Admin
        from models.user import User
        from models.parking_lot import ParkingLot
        from models.parking_spot import ParkingSpot
        from models.booking import Booking
        from models.vehicle import Vehicle
        
        # Create admin user
        admin = Admin(username='admin', password='admin123')
        db.session.add(admin)
        
        # Create test user
        test_user = User(
            username='user',
            email='user@example.com',
            password='user123',
            first_name='Test',
            last_name='User',
            phone='1234567890'
        )
        db.session.add(test_user)
        
        # Create sample parking lot
        parking_lot = ParkingLot(
            name='Main Street Parking',
            address='123 Main Street',
            pin_code='10001',
            price=2.50,
            total_spots=10,
            available_spots=10
        )
        db.session.add(parking_lot)
        db.session.commit()
        
        # Create sample parking spots
        for i in range(1, 11):
            spot_type = 'standard'
            if i == 1:
                spot_type = 'disabled'
            elif i == 2:
                spot_type = 'electric'
            
            spot = ParkingSpot(
                lot_id=parking_lot.id,
                spot_number=i,
                spot_type=spot_type
            )
            db.session.add(spot)
        
        # Create a sample vehicle for the test user
        vehicle = Vehicle(
            user_id=test_user.id,
            model='Toyota Camry',
            license_plate='ABC123',
            vehicle_type='standard',
            color='Blue'
        )
        db.session.add(vehicle)
        
        db.session.commit()
        
        print("Database recreated successfully!")
        print("Admin credentials: admin / admin123")
        print("User credentials: user@example.com / user123")

if __name__ == '__main__':
    recreate_database()
