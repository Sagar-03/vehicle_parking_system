#!/usr/bin/env python3
"""
Test script to verify the user dashboard functionality
"""

from app import create_app
from extensions import db
from models.user import User
from models.booking import Booking
from models.parking_spot import ParkingSpot

def test_user_dashboard():
    """Test if user dashboard query works without errors"""
    
    app = create_app()
    
    with app.app_context():
        # Get the test user
        user = User.query.filter_by(username='user').first()
        if not user:
            print("Test user not found!")
            return False
        
        print(f"Found user: {user.username} (ID: {user.id})")
        
        try:
            # Test the query that was failing
            active_booking = Booking.query.filter_by(
                user_id=user.id, 
                leaving_timestamp=None
            ).first()
            
            print(f"Active booking query successful: {active_booking}")
            
            # Test past bookings query
            past_bookings = Booking.query.filter(
                Booking.user_id == user.id,
                Booking.leaving_timestamp.isnot(None)
            ).order_by(Booking.leaving_timestamp.desc()).limit(5).all()
            
            print(f"Past bookings query successful: {len(past_bookings)} bookings found")
            
            # Test total bookings count
            total_bookings = Booking.query.filter_by(user_id=user.id).count()
            print(f"Total bookings count: {total_bookings}")
            
            print("All user dashboard queries working correctly!")
            return True
            
        except Exception as e:
            print(f"Error in user dashboard queries: {e}")
            return False

if __name__ == '__main__':
    test_user_dashboard()
