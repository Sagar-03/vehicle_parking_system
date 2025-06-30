import sqlite3

def inspect_table_schema(db_path, table_name):
    """Inspect the schema of a specific table in the SQLite database"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get table schema
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    
    print(f"\nTable: {table_name}")
    print("=" * 50)
    print("{:<5} {:<20} {:<10} {:<5} {:<20} {:<5}".format(
        "cid", "name", "type", "notnull", "default_value", "pk"
    ))
    print("-" * 50)
    for col in columns:
        print("{:<5} {:<20} {:<10} {:<5} {:<20} {:<5}".format(
            col[0], col[1], col[2], col[3], str(col[4]), col[5]
        ))
    
    conn.close()

if __name__ == "__main__":
    db_path = "instance/parking.db"
    inspect_table_schema(db_path, "booking")