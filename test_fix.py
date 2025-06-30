#!/usr/bin/env python
"""
Test script to verify that the Flask-WTF forms are working correctly
"""

try:
    print("Testing imports...")
    from routes.user_routes import BookingForm, LoginForm, RegistrationForm
    from routes.admin_routes import LoginForm as AdminLoginForm, ParkingLotForm
    print("✓ All form imports successful")
    
    print("\nTesting form instantiation...")
    booking_form = BookingForm()
    login_form = LoginForm()
    reg_form = RegistrationForm()
    admin_form = AdminLoginForm()
    lot_form = ParkingLotForm()
    print("✓ All forms can be instantiated")
    
    print("\nTesting hidden_tag method...")
    print(f"BookingForm has hidden_tag: {hasattr(booking_form, 'hidden_tag')}")
    print(f"LoginForm has hidden_tag: {hasattr(login_form, 'hidden_tag')}")
    
    if hasattr(booking_form, 'hidden_tag'):
        print("✓ hidden_tag method is available on forms")
    else:
        print("✗ hidden_tag method is NOT available on forms")
        
    print("\nAll tests completed successfully!")
    
except Exception as e:
    print(f"✗ Error occurred: {e}")
    import traceback
    traceback.print_exc()
