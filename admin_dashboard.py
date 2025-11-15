import streamlit as st
import pandas as pd
from utils import fetch_data, execute_query, call_procedure, display_product_card
from datetime import date
from db_connection import get_cursor, get_connection
import mysql.connector as mysql

def admin_dashboard():
    st.title("Admin Dashboard")
    st.sidebar.header("Admin Navigation")

    menu = ["Product Management", "Order Management", "Sales Reports", "Customer Management", "Category Management"]
    choice = st.sidebar.radio("Go to", menu)

    if choice == "Product Management":
        product_management_page()
    elif choice == "Order Management":
        order_management_page()
    elif choice == "Sales Reports":
        sales_reports_page()
    elif choice == "Customer Management":
        customer_management_page()
    elif choice == "Category Management":
        category_management_page()

def product_management_page():
    st.subheader("Product Management")

    st.write("### Add New Product")
    with st.form("add_product_form"):
        name = st.text_input("Product Name")
        description = st.text_area("Description")
        price = st.number_input("Price", min_value=0.0, format="%.2f")
        stock_quantity = st.number_input("Stock Quantity", min_value=0, step=1)
        
        categories = fetch_data("SELECT category_id, category_name FROM Category")
        category_map = {row['category_name']: row['category_id'] for _, row in categories.iterrows()}
        selected_category_name = st.selectbox("Category", list(category_map.keys()))
        category_id = category_map.get(selected_category_name)
        
        image_url = st.text_input("Image URL (optional)")

        submit_button = st.form_submit_button("Add Product")
        if submit_button:
            if not all([name, description, price is not None, stock_quantity is not None, category_id]):
                st.error("Please fill in all required fields.")
            else:
                success, msg = execute_query(
                    "INSERT INTO Product (name, description, price, stock_quantity, category_id, image_url) VALUES (%s, %s, %s, %s, %s, %s)",
                    (name, description, price, stock_quantity, category_id, image_url if image_url else None)
                )
                if success:
                    st.success("Product added successfully!")
                    st.rerun()
                else:
                    st.error(f"Failed to add product: {msg}")
    
    st.markdown("---")
    st.write("### Existing Products")
    products = fetch_data("SELECT p.product_id, p.name, p.description, p.price, p.stock_quantity, c.category_name, p.average_rating FROM Product p JOIN Category c ON p.category_id = c.category_id ORDER BY p.product_id DESC")
    
    if not products.empty:
        st.dataframe(products)
        
        st.write("#### Edit/Delete Product")
        product_ids = products['product_id'].tolist()
        selected_product_id = st.selectbox("Select Product ID to Edit/Delete:", product_ids)
        
        if selected_product_id:
            current_product = products[products['product_id'] == selected_product_id].iloc[0]

            with st.form("edit_product_form"):
                new_name = st.text_input("Product Name", value=current_product['name'])
                new_description = st.text_area("Description", value=current_product['description'])
                new_price = st.number_input("Price", min_value=0.0, value=float(current_product['price']), format="%.2f")
                new_stock_quantity = st.number_input("Stock Quantity", min_value=0, value=int(current_product['stock_quantity']), step=1)
                
                current_category_name = current_product['category_name']
                category_names = list(category_map.keys())
                selected_new_category_name = st.selectbox("Category", category_names, index=category_names.index(current_category_name))
                new_category_id = category_map.get(selected_new_category_name)
                
                update_button = st.form_submit_button("Update Product")
                delete_button = st.form_submit_button("Delete Product")

                if update_button:
                    success, msg = execute_query(
                        "UPDATE Product SET name = %s, description = %s, price = %s, stock_quantity = %s, category_id = %s WHERE product_id = %s",
                        (new_name, new_description, new_price, new_stock_quantity, new_category_id, selected_product_id)
                    )
                    if success:
                        st.success("Product updated successfully!")
                        st.rerun()
                    else:
                        st.error(f"Failed to update product: {msg}")
                
                if delete_button:
                    if st.warning("Are you sure you want to delete this product? This action cannot be undone."):
                        if st.button("Confirm Delete", key="confirm_delete_product"):
                            success, msg = execute_query("DELETE FROM Product WHERE product_id = %s", (selected_product_id,))
                            if success:
                                st.success("Product deleted successfully!")
                                st.rerun()
                            else:
                                st.error(f"Failed to delete product: {msg}")
    else:
        st.info("No products available.")

def order_management_page():
    st.subheader("Order Management")

    st.write("### All Orders")
    all_orders_df = fetch_data(
        """
        SELECT o.order_id, c.name AS customer_name, o.order_date, o.total_amount, o.status, o.shipping_address, o.delivery_date, p.payment_method, p.transaction_status
        FROM Orders o
        JOIN Customer c ON o.customer_id = c.customer_id
        LEFT JOIN Payment p ON o.order_id = p.order_id
        ORDER BY o.order_date DESC
        """
    )

    if not all_orders_df.empty:
        st.dataframe(all_orders_df)

        st.write("#### Update Order Status")
        order_ids = all_orders_df['order_id'].tolist()
        selected_order_id = st.selectbox("Select Order ID to Update:", order_ids)

        if selected_order_id:
            current_status = all_orders_df[all_orders_df['order_id'] == selected_order_id]['status'].iloc[0]

            # Map DB enum values (lowercase) to display labels
            status_values = ['pending', 'processing', 'shipped', 'delivered', 'cancelled']
            status_labels = ['Pending', 'Processing', 'Shipped', 'Delivered', 'Cancelled']

            # Ensure we have a safe index even if DB contains an unexpected value
            try:
                current_index = status_values.index(str(current_status).lower())
            except ValueError:
                current_index = 0

            selected_label = st.selectbox("New Status:", status_labels, index=current_index)
            # Convert label back to the underlying enum value used in the DB
            new_status = status_values[status_labels.index(selected_label)]

            if st.button("Update Order Status"):
                success, msg = call_procedure("update_order_status", (selected_order_id, new_status))
                if success:
                    st.success("Order status updated successfully!")
                    st.rerun()
                else:
                    st.error(f"Failed to update order status: {msg}")
    else:
        st.info("No orders found.")

def sales_reports_page():
    st.subheader("Sales Reports")

    st.write("### Generate Sales Report by Date Range")
    start_date = st.date_input("Start Date", value=date.today().replace(day=1))
    end_date = st.date_input("End Date", value=date.today())

    if st.button("Generate Report"):
        success, report_data = call_procedure("generate_sales_report", (start_date.isoformat(), end_date.isoformat()))
        if success and report_data:
            report_df = pd.DataFrame(report_data)
            st.dataframe(report_df)
            st.subheader("Sales Overview")
            st.metric("Total Revenue", f"₹{report_df['total_revenue'].sum():.2f}")
            st.metric("Total Orders", report_df['total_orders'].sum())
            st.metric("Unique Customers", report_df['unique_customers'].sum())
        else:
            st.info("No sales data for the selected period.")
    
    st.markdown("---")
    st.write("### Trending Products (Last 30 Days)")
    limit = st.slider("Number of Trending Products to Show:", 1, 20, 5)
    success, trending_products_data = call_procedure("get_trending_products", (limit,))

    if success and trending_products_data:
        trending_df = pd.DataFrame(trending_products_data)
        st.dataframe(trending_df)
        
        st.subheader("Top Selling Products (Graph)")
        if not trending_df.empty:
            st.bar_chart(trending_df.set_index('name')['total_quantity_sold'])
    else:
        st.info("No trending products found.")

def customer_management_page():
    st.subheader("Customer Management")
    st.write("### All Customers")
    customers_df = fetch_data("SELECT customer_id, name, email, phone, city, state, registration_date FROM Customer ORDER BY registration_date DESC")
    
    if not customers_df.empty:
        st.dataframe(customers_df)

        st.write("#### Customer Details and Actions")
        customer_ids = customers_df['customer_id'].tolist()
        selected_customer_id = st.selectbox("Select Customer ID:", customer_ids)

        if selected_customer_id:
            customer_data = customers_df[customers_df['customer_id'] == selected_customer_id].iloc[0]
            st.write(f"**Name:** {customer_data['name']}")
            st.write(f"**Email:** {customer_data['email']}")
            st.write(f"**Phone:** {customer_data['phone']}")
            st.write(f"**City:** {customer_data['city']}, {customer_data['state']}")
            st.write(f"**Registered On:** {customer_data['registration_date']}")

            st.write("##### Customer's Total Spending")
            # Call the get_customer_total_spending function
            cursor = get_cursor()
            try:
                cursor.execute("SELECT get_customer_total_spending(%s) AS total_spending", (selected_customer_id,))
                total_spent = cursor.fetchone()['total_spending']
                st.info(f"Total Amount Spent: ₹{total_spent:.2f}")
            except mysql.Error as err:
                st.error(f"Error fetching total spending: {err}")
            finally:
                cursor.close()
            
            st.write("##### Customer's Orders")
            success, customer_orders = call_procedure("get_customer_orders", (selected_customer_id,))
            if success and customer_orders:
                st.dataframe(pd.DataFrame(customer_orders))
            else:
                st.info("This customer has no orders.")
    else:
        st.info("No customers registered.")

def category_management_page():
    st.subheader("Category Management")
    
    st.write("### Add New Category")
    with st.form("add_category_form"):
        category_name = st.text_input("Category Name", key="new_category_name")
        description = st.text_area("Description", key="new_category_description")
        add_button = st.form_submit_button("Add Category")
        
        if add_button:
            if category_name:
                success, msg = execute_query(
                    "INSERT INTO Category (category_name, description) VALUES (%s, %s)",
                    (category_name, description)
                )
                if success:
                    st.success(f"Category '{category_name}' added successfully!")
                    st.rerun()
                else:
                    st.error(f"Failed to add category: {msg}")
            else:
                st.error("Category name cannot be empty.")
    
    st.markdown("---")
    st.write("### Existing Categories")
    categories_df = fetch_data("SELECT category_id, category_name, description FROM Category ORDER BY category_name")
    
    if not categories_df.empty:
        st.dataframe(categories_df)
        
        st.write("#### Edit/Delete Category")
        category_options = {row['category_name']: row['category_id'] for _, row in categories_df.iterrows()}
        selected_category_name = st.selectbox("Select Category to Edit/Delete:", ["-- Select Category --"] + list(category_options.keys()))

        if selected_category_name != "-- Select Category --":
            selected_category_id = category_options[selected_category_name]
            current_category = categories_df[categories_df['category_id'] == selected_category_id].iloc[0]

            st.markdown("---")
            st.write("#### Add Product to This Category")
            with st.form("add_product_in_category_form"):
                name = st.text_input("Product Name", key="cat_prod_name")
                description = st.text_area("Description", key="cat_prod_desc")
                price = st.number_input("Price", min_value=0.0, format="%.2f", key="cat_prod_price")
                stock_quantity = st.number_input("Stock Quantity", min_value=0, step=1, key="cat_prod_stock")
                st.text_input("Category", value=current_category['category_name'], disabled=True, key="cat_name_display")
                image_url = st.text_input("Image URL (optional)", key="cat_prod_image")

                add_product_btn = st.form_submit_button("Add Product to Category")
                if add_product_btn:
                    if not all([name, description, price is not None, stock_quantity is not None]):
                        st.error("Please fill in all required fields.")
                    else:
                        success, msg = execute_query(
                            "INSERT INTO Product (name, description, price, stock_quantity, category_id, image_url) VALUES (%s, %s, %s, %s, %s, %s)",
                            (name, description, price, stock_quantity, selected_category_id, image_url if image_url else None)
                        )
                        if success:
                            st.success(f"Product '{name}' added to category '{current_category['category_name']}' successfully!")
                            st.rerun()
                        else:
                            st.error(f"Failed to add product: {msg}")

            with st.form("edit_category_form"):
                new_category_name = st.text_input("Category Name", value=current_category['category_name'], key="edit_category_name")
                new_description = st.text_area("Description", value=current_category['description'], key="edit_category_description")
                
                update_button = st.form_submit_button("Update Category")
                delete_button = st.form_submit_button("Delete Category")

                if update_button:
                    success, msg = execute_query(
                        "UPDATE Category SET category_name = %s, description = %s WHERE category_id = %s",
                        (new_category_name, new_description, selected_category_id)
                    )
                    if success:
                        st.success(f"Category '{new_category_name}' updated successfully!")
                        st.rerun()
                    else:
                        st.error(f"Failed to update category: {msg}")
                
                if delete_button:
                    # Warning for deletion: Products in this category might become NULL
                    st.warning(f"Deleting category '{current_category['category_name']}' will set 'category_id' to NULL for associated products due to ON DELETE SET NULL constraint. Are you sure?")
                    if st.button("Confirm Delete Category", key="confirm_delete_category"):
                        success, msg = execute_query("DELETE FROM Category WHERE category_id = %s", (selected_category_id,))
                        if success:
                            st.success(f"Category '{current_category['category_name']}' deleted successfully!")
                            st.rerun()
                        else:
                            st.error(f"Failed to delete category: {msg}")
    else:
        st.info("No categories defined.")