import mysql.connector
import streamlit as st

# Database connection details
DB_CONFIG = {
    "host": "localhost",
    "user": "root", # Replace with your MySQL username
    "password": "g3JZhLeN", # Replace with your MySQL password
    "database": "online_shopping_db"
}

@st.cache_resource
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