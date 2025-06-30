"""
Migration script to add missing columns to the booking table
and migrate existing data from old column names to new ones.
"""
import sqlite3
import os

def migrate_booking_table():
    """Add missing columns to booking table and migrate data"""
    db_path = "instance/parking.db"
    
    if not os.path.exists(db_path):
        print("Database not found!")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if new columns already exist
        cursor.execute("PRAGMA table_info(booking)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Add parking_timestamp column if it doesn't exist
        if 'parking_timestamp' not in columns:
            cursor.execute("ALTER TABLE booking ADD COLUMN parking_timestamp DATETIME")
            print("Added parking_timestamp column")
            
            # Migrate data from start_time to parking_timestamp
            cursor.execute("UPDATE booking SET parking_timestamp = start_time WHERE start_time IS NOT NULL")
            print("Migrated data from start_time to parking_timestamp")
        
        # Add leaving_timestamp column if it doesn't exist
        if 'leaving_timestamp' not in columns:
            cursor.execute("ALTER TABLE booking ADD COLUMN leaving_timestamp DATETIME")
            print("Added leaving_timestamp column")
            
            # Migrate data from end_time to leaving_timestamp
            cursor.execute("UPDATE booking SET leaving_timestamp = end_time WHERE end_time IS NOT NULL")
            print("Migrated data from end_time to leaving_timestamp")
        
        # Add total_cost column if it doesn't exist
        if 'total_cost' not in columns:
            cursor.execute("ALTER TABLE booking ADD COLUMN total_cost FLOAT")
            print("Added total_cost column")
        
        conn.commit()
        print("Migration completed successfully!")
        
        # Show updated schema
        cursor.execute("PRAGMA table_info(booking)")
        columns = cursor.fetchall()
        
        print("\nUpdated booking table schema:")
        print("=" * 50)
        print("{:<5} {:<20} {:<10} {:<5} {:<20} {:<5}".format(
            "cid", "name", "type", "notnull", "default_value", "pk"
        ))
        print("-" * 50)
        for col in columns:
            print("{:<5} {:<20} {:<10} {:<5} {:<20} {:<5}".format(
                col[0], col[1], col[2], col[3], str(col[4]), col[5]
            ))
        
    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_booking_table()
