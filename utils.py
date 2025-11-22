import streamlit as st
import pandas as pd
import mysql.connector
from db_connection import get_cursor, get_connection
import os
import base64

def _to_native(value):
    try:
        return value.item()
    except Exception:
        return value

def _normalize_params(params):
    if params is None:
        return None
    try:
        return tuple(_to_native(p) for p in params)
    except TypeError:
        return params

def fetch_data(query, params=None):
    """Fetches data from the database using the given query."""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, _normalize_params(params))
        data = cursor.fetchall()
        return pd.DataFrame(data) if data else pd.DataFrame()
    except mysql.connector.Error as err:
        st.error(f"Database error: {err}")
        return pd.DataFrame()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

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

def call_procedure(procedure_name, params=()):
    """Calls a stored procedure."""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.callproc(procedure_name, params)
        
        # Get results
        results = []
        for result in cursor.stored_results():
            results.extend(result.fetchall())
        
        return pd.DataFrame(results) if results else pd.DataFrame()
    except mysql.connector.Error as err:
        st.error(f"Procedure error: {err}")
        return pd.DataFrame()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def display_product_card(product):
    """Display a product card in the UI."""
    col1, col2 = st.columns([1, 2])
    with col1:
        if product.get('image_url'):
            st.image(product['image_url'], width=150)
        else:
            st.image("https://via.placeholder.com/150", width=150)
    
    with col2:
        st.subheader(product['name'])
        st.write(product['description'][:200] + "..." if len(product['description']) > 200 else product['description'])
        st.write(f"**Price:** ${product['price']:.2f}")
        st.write(f"**Stock:** {product['stock_quantity']} units")
        
        if st.button(f"Add to Cart - {product['name']}", key=f"cart_{product['product_id']}"):
            if 'cart' not in st.session_state:
                st.session_state.cart = []
            
            # Check if product already in cart
            for item in st.session_state.cart:
                if item['product_id'] == product['product_id']:
                    item['quantity'] += 1
                    st.success(f"Added another {product['name']} to cart!")
                    return
            
            # Add new item to cart
            st.session_state.cart.append({
                'product_id': product['product_id'],
                'name': product['name'],
                'price': product['price'],
                'quantity': 1
            })
            st.success(f"Added {product['name']} to cart!")

def get_image_as_base64(image_path):
    """Convert image to base64 for embedding in HTML."""
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode()
    except FileNotFoundError:
        return None
