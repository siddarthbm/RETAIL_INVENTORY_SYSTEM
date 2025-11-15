#!/usr/bin/env python3
"""
Quick setup script to create stored procedures in the online_shopping_db.
"""

import subprocess
import sys

# Try to import mysql.connector, if not available, install it
try:
    import mysql.connector
except ImportError:
    print("Installing mysql-connector-python...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "mysql-connector-python"])
    import mysql.connector

from mysql.connector import Error

# Database connection details
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
        
        # First, reset DELIMITER to $$ and remove existing DELIMITER statements
        sql_content = sql_content.replace('DELIMITER $$\n', '').replace('DELIMITER ;', '')
        
        # Split by $$ to get individual statements
        statements = [stmt.strip() for stmt in sql_content.split('$$') if stmt.strip()]
        
        for i, statement in enumerate(statements):
            if not statement or statement.startswith('--'):
                continue
                
            print(f"\nExecuting statement {i+1}/{len(statements)}...")
            print(f"  {statement[:80]}...")
            
            try:
                # Remove any trailing semicolons
                statement = statement.rstrip(';').strip()
                cursor.execute(statement)
                connection.commit()
                print(f"  ✓ Success")
            except Error as e:
                if "already exists" in str(e):
                    print(f"  ⚠ Skipped (routine already exists)")
                    connection.rollback()
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
    sys.exit(0 if success else 1)
