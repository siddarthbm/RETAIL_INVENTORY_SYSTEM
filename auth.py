import streamlit as st
import bcrypt
from db_connection import get_connection, get_cursor
import mysql.connector as mysql

def hash_password(password):
    """Hashes a password using bcrypt."""
    hashed_bytes = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    return hashed_bytes.decode('utf-8')

def check_password(password, hashed_password):
    """Checks if a password matches its hash."""
    # For current demo schema, passwords are stored in plain text in the `password` column
    # so we just compare the raw values.
    return password == hashed_password

def register_user(name, email, phone, password, city, state, pin, address):
    """Registers a new customer."""
    conn = get_connection()
    cursor = get_cursor()
    try:
        cursor.execute(
            "INSERT INTO Customer (name, email, phone, password, city, state, pin, address) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            (name, email, phone, password, city, state, pin, address)
        )

        conn.commit()
        return True, "Registration successful!"
    except mysql.Error as err:
        conn.rollback()
        if "Duplicate entry" in str(err) and "email" in str(err):
            return False, "Email already registered."
        elif "Duplicate entry" in str(err) and "phone" in str(err):
            return False, "Phone number already registered."
        return False, f"Registration failed: {err}"
    finally:
        cursor.close()

def login_user(email, password):
    """Authenticates a user."""
    cursor = get_cursor()
    try:
        cursor.execute("SELECT customer_id, name, password FROM Customer WHERE email = %s", (email,))
        user = cursor.fetchone()
        if user and check_password(password, user['password']):
            return True, user

        else:
            return False, None
    except mysql.Error as err:
        st.error(f"Login error: {err}")
        return False, None
        cursor.close()

def logout_user():
    """Logs out the current user."""
    st.session_state['logged_in'] = False
    st.session_state['user_id'] = None
    st.session_state['user_name'] = None
    st.session_state['role'] = None 
    st.success("Logged out successfully.")

def login_page():
    """Displays the login/registration page."""
    st.subheader("Login / Register")

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
                        st.session_state['role'] = 'customer' # Default role for now
                        st.success(f"Welcome, {user_data['name']}!")
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