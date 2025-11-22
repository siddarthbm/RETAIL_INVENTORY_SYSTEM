import streamlit as st
import pandas as pd
from db_connection import fetch_data_as_df, execute_query

def customer_dashboard():
    st.title("🛍️ Customer Portal")
    st.sidebar.header("Customer Navigation")

    menu = ["🛒 Browse Products", "🛍️ Cart", "📦 My Orders", "👤 Profile"]
    choice = st.sidebar.radio("Go to", menu)

    if choice == "🛒 Browse Products":
        browse_products()
    elif choice == "🛍️ Cart":
        cart()
    elif choice == "📦 My Orders":
        my_orders()
    elif choice == "👤 Profile":
        profile()

def browse_products():
    st.subheader("🛒 Browse Products")
    
    # Search and filter
    col1, col2 = st.columns(2)
    with col1:
        search_term = st.text_input("Search products...")
    with col2:
        category_filter = st.selectbox("Filter by Category", ["All Categories"])
    
    # Get categories for filter
    categories = fetch_data_as_df("SELECT category_id, category_name FROM Category ORDER BY category_name")
    if not categories.empty:
        category_map = dict(zip(categories['category_name'], categories['category_id']))
        category_filter = st.selectbox("Filter by Category", ["All Categories"] + list(category_map.keys()))
    
    # Fetch products
    if category_filter == "All Categories":
        query = """
            SELECT p.product_id, p.name, p.description, p.price, p.stock_quantity, 
                   p.image_url, c.category_name
            FROM Product p
            LEFT JOIN Category c ON p.category_id = c.category_id
            WHERE p.stock_quantity > 0 AND p.status = 'active'
        """
        params = ()
    else:
        category_id = category_map.get(category_filter)
        query = """
            SELECT p.product_id, p.name, p.description, p.price, p.stock_quantity, 
                   p.image_url, c.category_name
            FROM Product p
            LEFT JOIN Category c ON p.category_id = c.category_id
            WHERE p.stock_quantity > 0 AND p.status = 'active' AND p.category_id = %s
        """
        params = (category_id,)
    
    if search_term:
        query += " AND (p.name LIKE %s OR p.description LIKE %s)"
        params = params + (f"%{search_term}%", f"%{search_term}%")
    
    query += " ORDER BY p.name"
    
    products = fetch_data_as_df(query, params)
    
    if not products.empty:
        st.write(f"Found {len(products)} products")
        
        # Display products in grid
        cols = st.columns(3)
        for idx, row in products.iterrows():
            with cols[idx % 3]:
                st.subheader(row['name'])
                if row['image_url']:
                    st.image(row['image_url'], width=200)
                st.write(row['description'][:100] + "..." if len(row['description']) > 100 else row['description'])
                st.write(f"**Price:** ${row['price']:.2f}")
                st.write(f"**Stock:** {row['stock_quantity']} units")
                st.write(f"**Category:** {row['category_name']}")
                
                if st.button(f"Add to Cart - {row['name']}", key=f"add_{row['product_id']}"):
                    add_to_cart(row['product_id'], row['name'], row['price'])
    else:
        st.info("No products found matching your criteria.")

def add_to_cart(product_id, product_name, price):
    """Add product to cart (simplified version)"""
    if 'cart' not in st.session_state:
        st.session_state.cart = []
    
    # Check if product already in cart
    for item in st.session_state.cart:
        if item['product_id'] == product_id:
            item['quantity'] += 1
            st.success(f"Added another {product_name} to cart!")
            return
    
    # Add new item to cart
    st.session_state.cart.append({
        'product_id': product_id,
        'name': product_name,
        'price': price,
        'quantity': 1
    })
    st.success(f"Added {product_name} to cart!")

def my_orders():
    st.subheader("📦 My Orders")
    
    customer_id = st.session_state.get('user_id')
    if not customer_id:
        st.error("Please login to view your orders.")
        return
    
    orders = fetch_data_as_df("""
        SELECT o.order_id, o.order_date, o.total_amount, o.status, 
               o.payment_status, o.payment_method
        FROM Orders o
        WHERE o.customer_id = %s
        ORDER BY o.order_date DESC
    """, (customer_id,))
    
    if not orders.empty:
        st.dataframe(orders, use_container_width=True)
        
        # Order details
        selected_order_id = st.selectbox("Select Order to View Details", orders['order_id'])
        
        if selected_order_id:
            order_items = fetch_data_as_df("""
                SELECT oi.order_item_id, p.name, oi.quantity, oi.price_at_purchase, oi.subtotal
                FROM Order_Item oi
                JOIN Product p ON oi.product_id = p.product_id
                WHERE oi.order_id = %s
            """, (selected_order_id,))
            
            if not order_items.empty:
                st.write("Order Items:")
                st.dataframe(order_items, use_container_width=True)
    else:
        st.info("You haven't placed any orders yet.")

def profile():
    st.subheader("👤 My Profile")

    customer_id = st.session_state.get('user_id')
    if not customer_id:
        st.error("Please login to view your profile.")
        return

    customer = fetch_data_as_df("""
        SELECT * FROM Customer WHERE customer_id = %s
    """, (customer_id,))

    if not customer.empty:
        user = customer.iloc[0]
        
        # Edit mode toggle
        edit_mode = st.checkbox("✏️ Edit Profile")
        
        if edit_mode:
            st.write("**Edit Your Information**")
            with st.form("edit_profile_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    name = st.text_input("Full Name", value=user['name'])
                    email = st.text_input("Email", value=user['email'])
                    phone = st.text_input("Phone", value=user['phone'])
                
                with col2:
                    city = st.text_input("City", value=user['city'])
                    state = st.text_input("State", value=user['state'])
                    pin = st.text_input("PIN Code", value=user['pin'])
                
                address = st.text_area("Address", value=user['address'])
                
                col1, col2 = st.columns(2)
                with col1:
                    submit_button = st.form_submit_button("💾 Save Changes", type="primary")
                with col2:
                    cancel_button = st.form_submit_button("❌ Cancel")
                
                if submit_button:
                    # Update profile
                    update_query = """
                        UPDATE Customer 
                        SET name = %s, email = %s, phone = %s, city = %s, state = %s, pin = %s, address = %s
                        WHERE customer_id = %s
                    """
                    try:
                        execute_query(update_query, (name, email, phone, city, state, pin, address, customer_id))
                        st.success("Profile updated successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error updating profile: {e}")
                
                if cancel_button:
                    st.rerun()
        else:
            # Display mode
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Personal Information**")
                st.write(f"Name: {user['name']}")
                st.write(f"Email: {user['email']}")
                st.write(f"Phone: {user['phone']}")

            with col2:
                st.write("**Address Information**")
                st.write(f"City: {user['city']}")
                st.write(f"State: {user['state']}")
                st.write(f"PIN: {user['pin']}")
                st.write(f"Address: {user['address']}")

            st.write(f"Member since: {user['created_at']}")
            
            # Order statistics
            order_stats = fetch_data_as_df("""
                SELECT 
                    COUNT(*) as total_orders,
                    SUM(total_amount) as total_spent,
                    MAX(order_date) as last_order_date
                FROM Orders 
                WHERE customer_id = %s
            """, (customer_id,))
            
            if not order_stats.empty:
                stats = order_stats.iloc[0]
                st.markdown("---")
                st.write("**Order Statistics**")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Orders", stats['total_orders'] or 0)
                with col2:
                    st.metric("Total Spent", f"${stats['total_spent'] or 0:.2f}")
                with col3:
                    st.metric("Last Order", stats['last_order_date'] or "Never")
    else:
        st.error("Profile not found.")

def cart():
    st.subheader("🛍️ Shopping Cart")
    
    if 'cart' not in st.session_state or not st.session_state.cart:
        st.info("Your cart is empty.")
        return
    
    cart_items = st.session_state.cart
    
    # Display cart items
    total_amount = 0
    for i, item in enumerate(cart_items):
        col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
        
        with col1:
            st.write(f"**{item['name']}**")
        
        with col2:
            quantity = st.number_input("Qty", min_value=1, value=item['quantity'], key=f"qty_{item['product_id']}")
            item['quantity'] = quantity
        
        with col3:
            st.write(f"${item['price']:.2f}")
        
        with col4:
            subtotal = item['price'] * item['quantity']
            st.write(f"${subtotal:.2f}")
            total_amount += subtotal
        
        with col5:
            if st.button("🗑️", key=f"remove_{item['product_id']}"):
                cart_items.pop(i)
                st.session_state.cart = cart_items
                st.rerun()
    
    st.markdown("---")
    st.write(f"**Total: ${total_amount:.2f}**")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Clear Cart"):
            st.session_state.cart = []
            st.rerun()
    
    with col2:
        if st.button("💳 Checkout", type="primary"):
            if st.session_state.get('logged_in'):
                # Create order
                customer_id = st.session_state.get('user_id')
                if customer_id and cart_items:
                    try:
                        # Insert order
                        order_query = """
                            INSERT INTO Orders (customer_id, order_date, total_amount, status, payment_status)
                            VALUES (%s, NOW(), %s, 'pending', 'pending')
                        """
                        result = execute_query(order_query, (customer_id, total_amount), fetch_one=True)
                        
                        if result:
                            order_id = result['order_id']
                            
                            # Insert order items
                            for item in cart_items:
                                item_query = """
                                    INSERT INTO Order_Item (order_id, product_id, quantity, price_at_purchase, subtotal)
                                    VALUES (%s, %s, %s, %s, %s)
                                """
                                execute_query(item_query, (order_id, item['product_id'], item['quantity'], item['price'], item['price'] * item['quantity']))
                            
                            # Update stock
                            for item in cart_items:
                                stock_query = "UPDATE Product SET stock_quantity = stock_quantity - %s WHERE product_id = %s"
                                execute_query(stock_query, (item['quantity'], item['product_id']))
                            
                            # Clear cart
                            st.session_state.cart = []
                            st.success(f"Order placed successfully! Order ID: {order_id}")
                            st.rerun()
                        else:
                            st.error("Failed to create order.")
                    except Exception as e:
                        st.error(f"Error during checkout: {e}")
            else:
                st.error("Please login to checkout.")
