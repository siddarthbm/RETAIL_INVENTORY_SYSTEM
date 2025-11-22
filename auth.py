import streamlit as st
from db_connection import get_connection, get_cursor
import mysql.connector as mysql

def register_user(name, email, phone, password, city, state, pin, address):
    """Registers a new customer for the retail inventory system."""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "INSERT INTO Customer (name, email, phone, password, city, state, pin, address) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            (name, email, phone, password, city, state, pin, address)
        )
        conn.commit()
        return True, "Registration successful!"
    except mysql.Error as err:
        if conn:
            conn.rollback()
        if "Duplicate entry" in str(err) and "email" in str(err):
            return False, "Email already registered."
        elif "Duplicate entry" in str(err) and "phone" in str(err):
            return False, "Phone number already registered."
        return False, f"Registration failed: {err}"
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def login_user(email, password):
    """Authenticates a user in the retail inventory system."""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT customer_id, name, password FROM Customer WHERE email = %s", (email,))
        user = cursor.fetchone()
        if user and password == user['password']:  # Plain text comparison
            return True, user
        else:
            return False, None
    except mysql.Error as err:
        st.error(f"Login error: {err}")
        return False, None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def logout_user():
    """Logs out the current user."""
    st.session_state['logged_in'] = False
    st.session_state['user_id'] = None
    st.session_state['user_name'] = None
    st.session_state['role'] = None
    st.success("Logged out successfully.")

def login_page():
    """Displays the login/registration page for retail inventory system."""
    st.subheader("Customer Login / Registration")

    login_tab, register_tab = st.tabs(["Login", "Register"])

    with login_tab:
        st.write("### Customer Login")
        with st.form("login_form"):
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            submit_button = st.form_submit_button("Login")
            
            if submit_button:
                if email and password:
                    success, user_data = login_user(email, password)
                    if success:
                        st.session_state['logged_in'] = True
                        st.session_state['user_id'] = user_data['customer_id']
                        st.session_state['user_name'] = user_data['name']
                        st.session_state['role'] = 'customer'
                        st.success(f"Welcome to Retail Inventory System, {user_data['name']}!")
                        st.rerun()
                    else:
                        st.error("Invalid email or password.")
                else:
                    st.error("Please enter both email and password.")
                    
    with register_tab:
        st.write("### New Customer Registration")
        with st.form("register_form"):
            name = st.text_input("Full Name", key="reg_name")
            email = st.text_input("Email", key="reg_email")
            phone = st.text_input("Phone", key="reg_phone")
            password = st.text_input("Password", type="password", key="reg_password")
            confirm_password = st.text_input("Confirm Password", type="password", key="reg_confirm_password")
            city = st.text_input("City", key="reg_city")
            state = st.text_input("State", key="reg_state")
            pin = st.text_input("PIN Code", key="reg_pin")
            address = st.text_area("Address", key="reg_address")
            submit_button = st.form_submit_button("Register")
            
            if submit_button:
                if password != confirm_password:
                    st.error("Passwords do not match.")
                elif not all([name, email, phone, password, city, state, pin, address]):
                    st.error("Please fill in all fields.")
                else:
                    success, message = register_user(name, email, phone, password, city, state, pin, address)
                    if success:
                        st.success(message + " You can now login.")
                    else:
                        st.error(message)