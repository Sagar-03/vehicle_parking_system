from extensions import db
from models.booking import Booking
import sqlite3
import os

print("Starting database column migration...")

# Path to SQLite database
db_path = 'instance/parking.db'
full_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), db_path)

print(f"Connecting to database at: {full_path}")

# Connect to the SQLite database
conn = sqlite3.connect(full_path)
cursor = conn.cursor()

try:
    # Check if the column exists
    cursor.execute("PRAGMA table_info(booking)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'vehicle_id' not in columns:
        print("Adding vehicle_id column to booking table...")
        # Add the vehicle_id column if it doesn't exist
        cursor.execute("ALTER TABLE booking ADD COLUMN vehicle_id INTEGER REFERENCES vehicle(id)")
        conn.commit()
        print("Column added successfully!")
    else:
        print("vehicle_id column already exists.")
    
except Exception as e:
    print(f"Error occurred: {str(e)}")
    conn.rollback()

# Close the connection
conn.close()

print("Migration completed!")