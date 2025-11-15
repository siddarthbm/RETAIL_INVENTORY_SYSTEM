#!/usr/bin/env python3
"""
Setup script to create stored procedures and functions in the online_shopping_db.
Run this once to initialize the database with required routines.
"""

import mysql.connector
from mysql.connector import Error

# Database connection details (same as db_connection.py)
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "g3JZhLeN",
    "database": "online_shopping_db"
}

def read_sql_file(filepath):
    """Read SQL statements from a file."""
    with open(filepath, 'r') as f:
        content = f.read()
    return content

def execute_sql_file(connection, filepath):
    """Execute SQL statements from a file."""
    cursor = connection.cursor()
    try:
        sql_content = read_sql_file(filepath)
        # Split by semicolon and filter empty statements
        statements = [stmt.strip() for stmt in sql_content.split('$$') if stmt.strip()]
        
        for i, statement in enumerate(statements):
            # Re-add $$ for DELIMITER statements if needed
            if 'DELIMITER' not in statement and statement:
                statement = statement + '$$'
            
            print(f"Executing statement {i+1}/{len(statements)}...")
            print(f"  {statement[:80]}...")
            
            try:
                cursor.execute(statement)
                connection.commit()
                print(f"  ✓ Success")
            except Error as e:
                if "already exists" in str(e):
                    print(f"  ⚠ Skipped (routine already exists)")
                else:
                    print(f"  ✗ Error: {e}")
                    connection.rollback()
        
        print("\n✓ Database setup completed!")
        return True
    except Exception as e:
        print(f"✗ Error reading or executing SQL file: {e}")
        return False
    finally:
        cursor.close()

def main():
    """Main setup function."""
    try:
        print("Connecting to database...")
        connection = mysql.connector.connect(**DB_CONFIG)
        print("✓ Connected to online_shopping_db\n")
        
        print("Creating stored procedures and functions...")
        sql_file = r"C:\Users\shukl\OneDrive\Desktop\DBMS\sql\create_stubs.sql"
        execute_sql_file(connection, sql_file)
        
        connection.close()
        print("✓ Connection closed")
    except Error as e:
        print(f"✗ Database error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
