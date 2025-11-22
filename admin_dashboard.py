import streamlit as st
import pandas as pd
from db_connection import fetch_data_as_df, execute_query
from datetime import date, timedelta

def admin_dashboard():
    st.title("🏢 Retail Inventory Management")
    st.sidebar.header("Admin Navigation")

    menu = ["📦 Inventory Overview", "➕ Product Management", "📊 Reports", "👥 Customer Management", "📦 Stock Management", "🛒 Order Management"]
    choice = st.sidebar.radio("Go to", menu)

    if choice == "📦 Inventory Overview":
        inventory_overview()
    elif choice == "➕ Product Management":
        product_management()
    elif choice == "📊 Reports":
        sales_reports()
    elif choice == "👥 Customer Management":
        customer_management()
    elif choice == "📦 Stock Management":
        stock_management()
    elif choice == "🛒 Order Management":
        order_management()

def inventory_overview():
    st.subheader("📦 Inventory Overview")
    
    # Get inventory summary
    try:
        products = fetch_data_as_df("""
            SELECT 
                COUNT(*) as total_products,
                SUM(stock_quantity) as total_stock,
                SUM(stock_quantity * price) as total_value,
                COUNT(CASE WHEN stock_quantity <= min_stock_level THEN 1 END) as low_stock_items,
                COUNT(CASE WHEN stock_quantity = 0 THEN 1 END) as out_of_stock_items
            FROM Product
        """)
        
        if not products.empty:
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.metric("Total Products", products.iloc[0]['total_products'])
            with col2:
                st.metric("Total Stock Items", int(products.iloc[0]['total_stock']))
            with col3:
                st.metric("Total Value", f"${products.iloc[0]['total_value']:,.2f}")
            with col4:
                st.metric("Low Stock Items", products.iloc[0]['low_stock_items'])
            with col5:
                st.metric("Out of Stock", products.iloc[0]['out_of_stock_items'])
        
        # Low stock alerts
        low_stock = fetch_data_as_df("""
            SELECT p.product_id, p.name, p.stock_quantity, p.min_stock_level, c.category_name
            FROM Product p
            JOIN Category c ON p.category_id = c.category_id
            WHERE p.stock_quantity <= p.min_stock_level
            ORDER BY p.stock_quantity ASC
            LIMIT 10
        """)
        
        if not low_stock.empty:
            st.warning("⚠️ Low Stock Alert - Items Need Reordering")
            st.dataframe(low_stock, use_container_width=True)
        
        # Recent inventory transactions
        transactions = fetch_data_as_df("""
            SELECT it.transaction_date, p.name, it.transaction_type, it.quantity_change, it.notes
            FROM Inventory_Transaction it
            JOIN Product p ON it.product_id = p.product_id
            ORDER BY it.transaction_date DESC
            LIMIT 10
        """)
        
        if not transactions.empty:
            st.subheader("📋 Recent Inventory Transactions")
            st.dataframe(transactions, use_container_width=True)
            
    except Exception as e:
        st.error(f"Error loading inventory overview: {e}")

def product_management():
    st.subheader("➕ Product Management")
    
    tab1, tab2, tab3 = st.tabs(["Add Product", "View Products", "Update Product"])
    
    with tab1:
        with st.form("add_product_form"):
            st.write("Add New Product")
            
            name = st.text_input("Product Name *")
            description = st.text_area("Description")
            price = st.number_input("Selling Price", min_value=0.0, format="%.2f")
            stock_quantity = st.number_input("Initial Stock", min_value=0, step=1)
            min_stock_level = st.number_input("Minimum Stock Level", min_value=0, step=1, value=10)
            sku = st.text_input("SKU (Stock Keeping Unit)")
            supplier = st.text_input("Supplier")
            cost_price = st.number_input("Cost Price", min_value=0.0, format="%.2f")
            
            categories = fetch_data_as_df("SELECT category_id, category_name FROM Category")
            if not categories.empty:
                category_map = dict(zip(categories['category_name'], categories['category_id']))
                selected_category_name = st.selectbox("Category", list(category_map.keys()))
                category_id = category_map.get(selected_category_name)
            else:
                st.error("No categories found. Please add categories first.")
                category_id = None
            
            submit_button = st.form_submit_button("Add Product")
            
            if submit_button:
                if name and price is not None and stock_quantity is not None and category_id:
                    success = execute_query("""
                        INSERT INTO Product (name, description, price, stock_quantity, min_stock_level, 
                                           category_id, sku, supplier, cost_price)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (name, description, price, stock_quantity, min_stock_level, category_id, sku, supplier, cost_price))
                    
                    if success is not None:
                        st.success("Product added successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to add product.")
                else:
                    st.error("Please fill in all required fields.")
    
    with tab2:
        st.write("View All Products")
        products = fetch_data_as_df("""
            SELECT p.product_id, p.name, p.description, p.price, p.stock_quantity, 
                   p.min_stock_level, p.sku, p.supplier, c.category_name, p.status
            FROM Product p
            LEFT JOIN Category c ON p.category_id = c.category_id
            ORDER BY p.product_id DESC
        """)
        
        if not products.empty:
            st.dataframe(products, use_container_width=True)
        else:
            st.info("No products found.")
    
    with tab3:
        st.write("Update Product")
        products = fetch_data_as_df("SELECT product_id, name FROM Product ORDER BY name")
        
        if not products.empty:
            product_map = dict(zip(products['name'], products['product_id']))
            selected_product_name = st.selectbox("Select Product to Update", list(product_map.keys()))
            selected_product_id = product_map.get(selected_product_name)
            
            if selected_product_id:
                current_product = fetch_data_as_df("""
                    SELECT * FROM Product WHERE product_id = %s
                """, (selected_product_id,))
                
                if not current_product.empty:
                    product = current_product.iloc[0]
                    
                    with st.form("update_product_form"):
                        new_name = st.text_input("Product Name", value=product['name'])
                        new_description = st.text_area("Description", value=product['description'] or "")
                        new_price = st.number_input("Price", min_value=0.0, value=float(product['price']), format="%.2f")
                        new_stock = st.number_input("Stock Quantity", min_value=0, value=int(product['stock_quantity']))
                        new_min_stock = st.number_input("Min Stock Level", min_value=0, value=int(product['min_stock_level']))
                        
                        categories = fetch_data_as_df("SELECT category_id, category_name FROM Category")
                        if not categories.empty:
                            category_map = dict(zip(categories['category_name'], categories['category_id']))
                            current_category = categories[categories['category_id'] == product['category_id']]['category_name'].iloc[0] if product['category_id'] else ""
                            new_category_name = st.selectbox("Category", list(category_map.keys()), index=list(category_map.keys()).index(current_category) if current_category in category_map else 0)
                            new_category_id = category_map.get(new_category_name)
                        
                        update_button = st.form_submit_button("Update Product")
                        
                        if update_button:
                            success = execute_query("""
                                UPDATE Product SET name=%s, description=%s, price=%s, stock_quantity=%s, 
                                                   min_stock_level=%s, category_id=%s
                                WHERE product_id=%s
                            """, (new_name, new_description, new_price, new_stock, new_min_stock, new_category_id, selected_product_id))
                            
                            if success is not None:
                                st.success("Product updated successfully!")
                                st.rerun()
                            else:
                                st.error("Failed to update product.")
        else:
            st.info("No products available to update.")

def stock_management():
    st.subheader("📦 Stock Management")
    
    tab1, tab2 = st.tabs(["Update Stock", "Stock Transactions"])
    
    with tab1:
        st.write("Update Product Stock")
        
        products = fetch_data_as_df("SELECT product_id, name, stock_quantity FROM Product ORDER BY name")
        if not products.empty:
            product_map = dict(zip(products['name'], products['product_id']))
            selected_product_name = st.selectbox("Select Product", list(product_map.keys()))
            selected_product_id = product_map.get(selected_product_name)
            
            if selected_product_id:
                current_stock = products[products['product_id'] == selected_product_id]['stock_quantity'].iloc[0]
                st.info(f"Current Stock: {current_stock}")
                
                with st.form("update_stock_form"):
                    transaction_type = st.selectbox("Transaction Type", ["Purchase (Stock In)", "Sale (Stock Out)", "Adjustment", "Return", "Damage"])
                    quantity_change = st.number_input("Quantity Change", min_value=1, step=1)
                    notes = st.text_area("Notes")
                    
                    submit_button = st.form_submit_button("Update Stock")
                    
                    if submit_button:
                        # Convert transaction type to database value
                        transaction_map = {
                            "Purchase (Stock In)": "purchase",
                            "Sale (Stock Out)": "sale", 
                            "Adjustment": "adjustment",
                            "Return": "return",
                            "Damage": "damage"
                        }
                        
                        db_transaction_type = transaction_map.get(transaction_type, "adjustment")
                        actual_change = quantity_change if db_transaction_type in ["purchase", "return"] else -quantity_change
                        
                        success = execute_query("""
                            UPDATE Product SET stock_quantity = stock_quantity + %s 
                            WHERE product_id = %s
                        """, (actual_change, selected_product_id))
                        
                        if success is not None:
                            # Record inventory transaction
                            execute_query("""
                                INSERT INTO Inventory_Transaction 
                                (product_id, transaction_type, quantity_change, reference_type, notes, stock_before, stock_after)
                                VALUES (%s, %s, %s, 'manual', %s, %s, %s)
                            """, (selected_product_id, db_transaction_type, actual_change, notes, current_stock, current_stock + actual_change))
                            
                            st.success(f"Stock updated successfully! New stock: {current_stock + actual_change}")
                            st.rerun()
                        else:
                            st.error("Failed to update stock.")
        else:
            st.info("No products found.")
    
    with tab2:
        st.write("Recent Stock Transactions")
        transactions = fetch_data_as_df("""
            SELECT it.transaction_date, p.name, it.transaction_type, it.quantity_change, 
                   it.stock_before, it.stock_after, it.notes
            FROM Inventory_Transaction it
            JOIN Product p ON it.product_id = p.product_id
            ORDER BY it.transaction_date DESC
            LIMIT 50
        """)
        
        if not transactions.empty:
            st.dataframe(transactions, use_container_width=True)
        else:
            st.info("No transactions found.")

def sales_reports():
    st.subheader("📊 Sales Reports")
    
    # Date range selector
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", date.today() - timedelta(days=30))
    with col2:
        end_date = st.date_input("End Date", date.today())
    
    tab1, tab2, tab3 = st.tabs(["Sales Summary", "Top Products", "Category Performance"])
    
    with tab1:
        try:
            sales_data = fetch_data_as_df("""
                CALL GetSalesReport(%s, %s)
            """, (start_date, end_date))
            
            if not sales_data.empty:
                st.dataframe(sales_data, use_container_width=True)
                
                # Summary metrics
                total_revenue = sales_data['total_revenue'].sum()
                total_orders = sales_data['total_orders'].sum()
                avg_order_value = sales_data['average_order_value'].mean()
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Revenue", f"${total_revenue:,.2f}")
                with col2:
                    st.metric("Total Orders", int(total_orders))
                with col3:
                    st.metric("Avg Order Value", f"${avg_order_value:.2f}")
            else:
                st.info("No sales data found for the selected period.")
        except Exception as e:
            st.error(f"Error loading sales data: {e}")
    
    with tab2:
        try:
            top_products = fetch_data_as_df("CALL GetTopSellingProducts(10)")
            
            if not top_products.empty:
                st.dataframe(top_products, use_container_width=True)
            else:
                st.info("No product sales data found.")
        except Exception as e:
            st.error(f"Error loading top products: {e}")
    
    with tab3:
        try:
            category_sales = fetch_data_as_df("""
                SELECT 
                    c.category_name,
                    COUNT(DISTINCT o.order_id) as orders,
                    SUM(oi.quantity) as items_sold,
                    SUM(oi.subtotal) as revenue
                FROM Category c
                JOIN Product p ON c.category_id = p.category_id
                JOIN Order_Item oi ON p.product_id = oi.product_id
                JOIN Orders o ON oi.order_id = o.order_id
                WHERE DATE(o.order_date) BETWEEN %s AND %s
                  AND o.status != 'cancelled'
                GROUP BY c.category_id, c.category_name
                ORDER BY revenue DESC
            """, (start_date, end_date))
            
            if not category_sales.empty:
                st.dataframe(category_sales, use_container_width=True)
            else:
                st.info("No category sales data found.")
        except Exception as e:
            st.error(f"Error loading category data: {e}")

def customer_management():
    st.subheader("👥 Customer Management")
    
    customers = fetch_data_as_df("""
        SELECT customer_id, name, email, phone, city, state, created_at
        FROM Customer
        ORDER BY created_at DESC
    """)
    
    if not customers.empty:
        st.dataframe(customers, use_container_width=True)
    else:
        st.info("No customers found.")

def order_management():
    st.subheader("🛒 Order Management")
    
    orders = fetch_data_as_df("""
        SELECT o.order_id, c.name as customer_name, o.order_date, o.total_amount, 
               o.status, o.payment_status, o.payment_method
        FROM Orders o
        JOIN Customer c ON o.customer_id = c.customer_id
        ORDER BY o.order_date DESC
    """)
    
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
        st.info("No orders found.")
