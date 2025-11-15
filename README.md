# ONLINE_STORE_MANAGEMENT
Online Shopping Database Management System A full-stack e-commerce application built with Streamlit and MySQL, featuring a dual-role system for customers and administrators to manage an online store with shopping carts, orders, and inventory management.
Key Features
✨ Customer Features:

User registration and secure authentication (bcrypt password hashing)
Browse products by category
Add/remove items from shopping cart
Place orders with shipping address
View order history and status
Add products to wishlist
Submit product reviews and ratings

👨‍💼 Admin Features:

Manage product inventory (add, update, delete)
View all customer orders and order status
Monitor product categories
Track customer activity
Manage shipping and delivery status

🔒 Core Functionality:

Secure user authentication and role-based access control
Real-time cart management
Order processing workflow (pending → processing → shipped → delivered)
Product inventory management with stock validation
Customer reviews and ratings system
Wishlist management
Technology Stack
Frontend: Streamlit (web UI)
Backend: Python
Database: MySQL with stored procedures
Authentication: bcrypt password hashing
Dependencies: streamlit, mysql-connector-python, bcrypt

Project Structure
DBMS/
├── app.py                  # Main Streamlit application
├── auth.py                 # Authentication logic
├── customer_dashboard.py   # Customer interface
├── admin_dashboard.py      # Admin interface
├── db_connection.py        # MySQL connection handler
├── utils.py                # Utility functions
├── setup_database.py       # Database initialization
├── run_setup.py            # Setup runner
├── requirements.txt        # Python dependencies
└── sql/
    ├── full_schema.sql     # Database schema & tables
    └── seed_data.sql       # Sample data

Database Schema
Customer: User accounts with contact and address info
Product: Catalog with pricing, stock, and ratings
Category: Product categorization
Cart/Cart_Item: Shopping cart management
Orders: Order tracking with multiple statuses
Review: Customer ratings and reviews
Wishlist: Save favorite products

Getting Started
Install MySQL and create database
Install Python dependencies: pip install -r requirements.txt
Configure database connection in db_connection.py
Run python setup_database.py to initialize schema
Launch app: streamlit run app.py
