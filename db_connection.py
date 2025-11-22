import mysql.connector
import streamlit as st
import pandas as pd

# Database connection details
DB_CONFIG = {
    "host": "localhost",
    "user": "root", # Replace with your MySQL username
    "password": "g3JZhLeN", # Replace with your MySQL password
    "database": "retail_db"
}

def get_connection():
    """Establishes and returns a connection to the MySQL database."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as err:
        st.error(f"Error connecting to database: {err}")
        st.stop()

def get_cursor():
    """Returns a cursor object from the database connection."""
    conn = get_connection()
    return conn.cursor(dictionary=True) # Use dictionary=True for easier data access

def execute_query(query, params=(), fetch_one=False, fetch_all=False):
    """Execute a SQL query with proper error handling."""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params)
        conn.commit()
        
        if fetch_one:
            return cursor.fetchone()
        elif fetch_all:
            return cursor.fetchall()
        return None  # For INSERT, UPDATE, DELETE
    except mysql.connector.Error as err:
        st.error(f"Database error: {err}")
        if conn:
            conn.rollback()
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def fetch_data_as_df(query, params=()):
    """Execute query and return results as pandas DataFrame."""
    conn = None
    try:
        conn = get_connection()
        df = pd.read_sql_query(query, conn, params=params)
        return df
    except mysql.connector.Error as err:
        st.error(f"Database error: {err}")
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()