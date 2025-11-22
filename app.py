import streamlit as st
from auth import login_page, logout_user
from customer_dashboard import customer_dashboard
from admin_dashboard import admin_dashboard
from db_connection import get_connection # To ensure connection is attempted on startup

# Set page configuration
st.set_page_config(
    page_title="Retail Inventory Management",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)



# Initialize session state for authentication
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user_id' not in st.session_state:
    st.session_state['user_id'] = None
if 'user_name' not in st.session_state:
    st.session_state['user_name'] = None
if 'role' not in st.session_state:
    st.session_state['role'] = None # 'customer' or 'admin'

# Attempt to connect to DB at startup (will show error if failed)
try:
    get_connection()
    # st.success("Database connected successfully!") # Uncomment for debugging connection
except Exception as e:
    st.error(f"Failed to connect to the database. Please ensure MySQL is running and configured correctly. Error: {e}")
    st.stop()


# Main application logic
def main():
    st.sidebar.title("Retail Inventory Management")

    if st.session_state['logged_in']:
        st.sidebar.write(f"Logged in as: **{st.session_state['user_name']}** ({st.session_state['role'].capitalize()})")
        if st.sidebar.button("Logout"):
            logout_user()
            st.rerun()

        if st.session_state['role'] == 'customer':
            customer_dashboard()
        elif st.session_state['role'] == 'admin':
            admin_dashboard() # Implement admin_dashboard functionality
        else:
            st.error("Unknown user role. Please log in again.")
            logout_user()
            st.rerun()

    else:
        st.sidebar.info("Please login or register to continue.")
        login_page()

        # Simple admin login for demonstration (You'd want a more secure system)
        st.sidebar.markdown("---")
        st.sidebar.subheader("Admin Login (Demo)")
        admin_email = st.sidebar.text_input("Admin Email", key="admin_email_input")
        admin_password = st.sidebar.text_input("Admin Password", type="password", key="admin_password_input")
        if st.sidebar.button("Admin Login"):
            # A very simple admin check. In a real app, you'd have an Admin table
            if admin_email == "admin@retail.com" and admin_password == "admin123": # REPLACE WITH SECURE ADMIN CREDENTIALS
                st.session_state['logged_in'] = True
                st.session_state['user_id'] = 0 # Admin user_id can be 0 or a dedicated ID
                st.session_state['user_name'] = "Administrator"
                st.session_state['role'] = 'admin'
                st.success("Admin logged in successfully!")
                st.rerun()
            else:
                st.sidebar.error("Invalid Admin credentials.")

if __name__ == "__main__":
    main()