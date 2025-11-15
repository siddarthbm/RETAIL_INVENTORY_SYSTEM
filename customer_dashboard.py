import streamlit as st
import pandas as pd
from utils import fetch_data, execute_query, call_procedure, display_product_card, display_order_item_card, get_categories
from db_connection import get_cursor, get_connection
import os
import base64

def customer_dashboard():
    st.title(f"Welcome, {st.session_state['user_name']}!")
    st.sidebar.header("Customer Navigation")

    menu = ["Browse Products", "My Cart", "My Orders", "My Wishlist", "My Reviews", "Profile"]
    choice = st.sidebar.radio("Go to", menu)

    if choice == "Browse Products":
        browse_products_page()
    elif choice == "My Cart":
        my_cart_page()
    elif choice == "My Orders":
        my_orders_page()
    elif choice == "My Wishlist":
        my_wishlist_page()
    elif choice == "My Reviews":
        my_reviews_page()
    elif choice == "Profile":
        customer_profile_page()


def browse_products_page():
    st.subheader("Explore Our Products")

    categories_df = get_categories()
    category_names = ["All Products"] + list(categories_df['category_name'])
    selected_category_tab = st.tabs(category_names)

    col_search, col_dbg = st.columns([3, 1])
    with col_search:
        search_term = st.text_input("Search products by name:", key="product_search_term")
    with col_dbg:
        st.session_state['debug_images'] = st.checkbox("Debug images", value=st.session_state.get('debug_images', False))

    col_price_min, col_price_max = st.columns(2)
    with col_price_min:
        min_price = st.number_input("Min Price:", min_value=0.0, value=0.0, key="min_price_input")
    with col_price_max:
        max_price = st.number_input("Max Price:", min_value=0.0, value=500000.0, key="max_price_input")

    for i, tab in enumerate(selected_category_tab):
        with tab:
            current_category_name = category_names[i]
            st.write(f"### {current_category_name}")

            selected_category_id = None
            if current_category_name != "All Products":
                selected_category_id = categories_df[categories_df['category_name'] == current_category_name]['category_id'].iloc[0]

            success, products_data = call_procedure(
                "search_products",
                (f"%{search_term}%" if search_term else None,
                 selected_category_id,
                 min_price if min_price > 0 else None,
                 max_price if max_price < 500000 else None)
            )

            if not success:
                st.error(f"Failed to fetch products: {products_data}")
            elif products_data:
                products_df = pd.DataFrame(products_data)
                cols = st.columns(4)

                for j, row in products_df.iterrows():
                    with cols[j % 4]:
                        display_product_card(row)
                        if row['stock_quantity'] > 0:
                            quantity = st.number_input(f"Qty for {row['product_id']}",
                                min_value=1, max_value=row['stock_quantity'], value=1,
                                key=f"{current_category_name}_qty_{row['product_id']}"
                            )
                            col_add, col_wish = st.columns(2)

                            with col_add:
                                if st.button("Add to Cart", key=f"{current_category_name}_add_{row['product_id']}"):
                                    success_add, msg_add = call_procedure(
                                        "add_to_cart",
                                        (st.session_state['user_id'], row['product_id'], quantity)
                                    )
                                    if success_add:
                                        st.success(f"{quantity} x {row['name']} added to cart!")
                                    else:
                                        st.error(f"Failed to add to cart: {msg_add}")

                            with col_wish:
                                if st.button("Add to Wishlist", key=f"{current_category_name}_wish_{row['product_id']}"):
                                    wishlist_success, wishlist_msg = execute_query(
                                        "INSERT INTO Wishlist (customer_id, product_id) VALUES (%s, %s) "
                                        "ON DUPLICATE KEY UPDATE added_date=CURRENT_TIMESTAMP",
                                        (st.session_state['user_id'], row['product_id'])
                                    )
                                    if wishlist_success:
                                        st.success(f"{row['name']} added to wishlist!")
                                    else:
                                        st.error(f"Failed: {wishlist_msg}")
                        else:
                            st.info("Product out of stock.")
            else:
                st.info("No products found.")


def my_cart_page():
    st.subheader("My Shopping Cart")
    user_id = st.session_state['user_id']

    # Fetch cart items
    cart_items_df = fetch_data(
        """
        SELECT ci.cart_item_id, ci.product_id, p.name, p.price,
               ci.quantity, (ci.quantity * p.price) AS item_total,
               p.stock_quantity, p.image_url
        FROM Cart_Item ci
        JOIN Cart c ON ci.cart_id = c.cart_id
        JOIN Product p ON ci.product_id = p.product_id
        WHERE c.customer_id = %s
        """,
        (user_id,)
    )

    # -----------------------------------------------------------
    # ⭐ NESTED QUERY ADDED HERE (Cheapest Alternative Product)
    # -----------------------------------------------------------

    product_in_cart = fetch_data(
        """
        SELECT p.product_id, p.category_id, p.price
        FROM Cart_Item ci
        JOIN Cart c ON ci.cart_id = c.cart_id
        JOIN Product p ON ci.product_id = p.product_id
        WHERE c.customer_id = %s
        LIMIT 1
        """,
        (user_id,)
    )

    if not product_in_cart.empty:
        nested_alt_df = fetch_data(
            """
            SELECT name AS alternative_name, price AS alternative_price
            FROM Product
            WHERE category_id = %s
              AND price < %s
              AND product_id != %s
              AND price = (
                    SELECT MIN(price)
                    FROM Product
                    WHERE category_id = %s
                      AND price < %s
              );
            """,
            (
                product_in_cart.iloc[0]['category_id'],
                product_in_cart.iloc[0]['price'],
                product_in_cart.iloc[0]['product_id'],
                product_in_cart.iloc[0]['category_id'],
                product_in_cart.iloc[0]['price']
            )
        )

        if not nested_alt_df.empty:
            st.info(
                f"Cheaper alternative found: **{nested_alt_df.iloc[0]['alternative_name']}** "
                f"(₹{nested_alt_df.iloc[0]['alternative_price']})"
            )

    # -----------------------------------------------------------

    if not cart_items_df.empty:
        total_cart_value = cart_items_df['item_total'].sum()
        st.write(f"You have {len(cart_items_df)} items. Total: ₹{total_cart_value:.2f}")

        for i, item in cart_items_df.iterrows():
            col1, col2, col3, col4 = st.columns([0.5, 2, 1, 1])

            with col1:
                original_image = item.get('image_url')
                image_src = original_image if original_image else None
                if isinstance(image_src, str):
                    is_web = image_src.startswith("http")
                    is_file = os.path.exists(image_src)
                    if not (is_web or is_file):
                        base_dir = os.path.dirname(__file__)
                        candidates = [
                            os.path.join(base_dir, "images", image_src),
                            os.path.join(base_dir, "assets", image_src),
                        ]
                        resolved = next((p for p in candidates if os.path.exists(p)), None)
                        image_src = resolved if resolved else None
                else:
                    image_src = None

                _placeholder_png_sm = base64.b64decode(
                    "iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAQAAACEN3D/AAAADElEQVR4nGMAAQAABQAB8k5EAgAAAABJRU5ErkJggg=="
                )

                try:
                    if image_src:
                        st.image(image_src, width=50)
                    else:
                        st.image(_placeholder_png_sm, width=50)
                except:
                    st.image(_placeholder_png_sm, width=50)

            with col2:
                st.write(f"**{item['name']}**")
                st.write(f"Price: ₹{item['price']:.2f}")

            with col3:
                new_quantity = st.number_input(
                    f"Quantity",
                    min_value=1,
                    max_value=item['stock_quantity'],
                    value=item['quantity'],
                    key=f"cart_qty_{item['cart_item_id']}"
                )
                if new_quantity != item['quantity']:
                    success, msg = execute_query(
                        "UPDATE Cart_Item SET quantity = %s WHERE cart_item_id = %s",
                        (new_quantity, item['cart_item_id'])
                    )
                    if success:
                        st.success("Updated successfully.")
                        st.rerun()
                    else:
                        st.error(msg)

            with col4:
                st.write(f"Subtotal: ₹{item['item_total']:.2f}")
                if st.button("Remove", key=f"remove_cart_{item['cart_item_id']}"):
                    success, msg = execute_query(
                        "DELETE FROM Cart_Item WHERE cart_item_id = %s",
                        (item['cart_item_id'],)
                    )
                    if success:
                        st.success("Item removed.")
                        st.rerun()
                    else:
                        st.error(msg)

            st.markdown("---")

        st.subheader("Checkout")
        address_df = fetch_data(
            "SELECT address FROM Customer WHERE customer_id = %s",
            (user_id,)
        )
        default_address = "" if address_df.empty else address_df.iloc[0]['address']

        shipping_address = st.text_area("Shipping Address", value=default_address)
        payment_method = st.selectbox(
            "Payment Method",
            ['Credit Card', 'Debit Card', 'UPI', 'Net Banking', 'Cash on Delivery']
        )

        if st.button("Place Order", disabled=(not shipping_address or total_cart_value == 0)):
            success, results = call_procedure(
                "place_order",
                (user_id, shipping_address, payment_method)
            )
            if success:
                st.success("Order placed successfully!")
                st.balloons()
                st.rerun()
            else:
                st.error(results)

    else:
        st.info("Your cart is empty.")


# ----------------------------------------------------------------------
# Remaining functions (my_orders_page, my_wishlist_page, my_reviews_page,
# customer_profile_page) remain exactly the same as your existing code.
# ----------------------------------------------------------------------





















def my_orders_page():
    st.subheader("My Orders")
    user_id = st.session_state['user_id']

    success, orders_data = call_procedure("get_customer_orders", (user_id,))
    
    if success and orders_data:
        orders_df = pd.DataFrame(orders_data)
        st.write(f"You have {len(orders_df)} past orders.")

        for i, order in orders_df.iterrows():
            with st.expander(f"Order ID: {order['order_id']} | Date: {order['order_date']} | Total: ₹{order['total_amount']:.2f} | Status: {order['status']}"):
                # Need to fetch shipping_address separately as get_customer_orders SP doesn't return it
                order_details = fetch_data("SELECT shipping_address FROM Orders WHERE order_id = %s", (order['order_id'],))
                if not order_details.empty:
                    st.write(f"**Shipping Address:** {order_details.iloc[0]['shipping_address']}")
                
                st.write(f"**Payment Method:** {order['payment_method']}")
                st.write(f"**Transaction Status:** {order['transaction_status']}")
                if order['delivery_date']:
                    st.write(f"**Delivery Date:** {order['delivery_date']}")
                
                # Fetch order items for this specific order
                order_items_df = fetch_data(
                    """
                    SELECT oi.quantity, oi.price_at_purchase, oi.subtotal, p.name AS product_name, p.image_url
                    FROM Order_Item oi
                    JOIN Product p ON oi.product_id = p.product_id
                    WHERE oi.order_id = %s
                    """,
                    (order['order_id'],)
                )
                if not order_items_df.empty:
                    st.write("---")
                    st.write("**Items in this order:**")
                    for _, item in order_items_df.iterrows():
                        col_item_img, col_item_details = st.columns([0.5, 3])
                        with col_item_img:
                            original_image = item.get('image_url')
                            image_src = original_image if original_image else None
                            if isinstance(image_src, str):
                                is_web = image_src.startswith("http://") or image_src.startswith("https://")
                                is_file = os.path.exists(image_src)
                                if not (is_web or is_file):
                                    base_dir = os.path.dirname(__file__)
                                    candidates = [
                                        os.path.join(base_dir, "images", image_src),
                                        os.path.join(base_dir, "assets", image_src),
                                        os.path.join(base_dir, "assets", "images", image_src),
                                        os.path.join(base_dir, "PICTURES", image_src),
                                        os.path.join(os.getcwd(), "images", image_src),
                                        os.path.join(os.getcwd(), "assets", image_src),
                                        os.path.join(os.getcwd(), "assets", "images", image_src),
                                        os.path.join(os.getcwd(), "PICTURES", image_src),
                                    ]
                                    resolved = next((p for p in candidates if os.path.exists(p)), None)
                                    image_src = resolved if resolved else None
                            else:
                                image_src = None
                            _placeholder_png_sm = base64.b64decode(
                                "iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAQAAACEN3D/AAAADElEQVR4nGMAAQAABQAB8k5EAgAAAABJRU5ErkJggg=="
                            )
                            try:
                                if image_src:
                                    st.image(image_src, width=50)
                                else:
                                    st.image(_placeholder_png_sm, width=50)
                            except Exception:
                                st.image(_placeholder_png_sm, width=50)
                        with col_item_details:
                            display_order_item_card(item)
                else:
                    st.info("No items found for this order.")
            st.markdown("---")
    else:
        st.info("You haven't placed any orders yet.")

def my_wishlist_page():
    st.subheader("My Wishlist")
    user_id = st.session_state['user_id']

    wishlist_df = fetch_data(
        """
        SELECT w.product_id, p.name, p.description, p.price, p.stock_quantity, p.average_rating, p.image_url
        FROM Wishlist w
        JOIN Product p ON w.product_id = p.product_id
        WHERE w.customer_id = %s
        """,
        (user_id,)
    )

    if not wishlist_df.empty:
        st.write(f"You have {len(wishlist_df)} items in your wishlist.")
        cols = st.columns(4) # Display 4 products per row
        for i, row in wishlist_df.iterrows():
            with cols[i % 4]:
                display_product_card(row)
                col_add, col_rem = st.columns(2)
                with col_add:
                    if row['stock_quantity'] > 0:
                        if st.button("Add to Cart", key=f"wish_add_cart_{row['product_id']}"):
                            success_add, msg_add = call_procedure("add_to_cart", (user_id, row['product_id'], 1)) # Add 1 by default
                            if success_add:
                                st.success(f"{row['name']} added to cart!")
                            else:
                                st.error(f"Failed to add to cart: {msg_add}")
                    else:
                        st.info("Out of Stock")
                with col_rem:
                    if st.button("Remove from Wishlist", key=f"remove_wish_{row['product_id']}"):
                        success, msg = execute_query(
                            "DELETE FROM Wishlist WHERE customer_id = %s AND product_id = %s",
                            (user_id, row['product_id'])
                        )
                        if success:
                            st.success("Item removed from wishlist.")
                            st.rerun()
                        else:
                            st.error(f"Failed to remove item: {msg}")
    else:
        st.info("Your wishlist is empty.")

def my_reviews_page():
    st.subheader("My Product Reviews")
    user_id = st.session_state['user_id']

    my_reviews_df = fetch_data(
        """
        SELECT r.review_id, r.product_id, p.name AS product_name, r.rating, r.comment, r.review_date
        FROM Review r
        JOIN Product p ON r.product_id = p.product_id
        WHERE r.customer_id = %s
        ORDER BY r.review_date DESC
        """,
        (user_id,)
    )

    if not my_reviews_df.empty:
        st.write(f"You have written {len(my_reviews_df)} reviews.")
        for i, review in my_reviews_df.iterrows():
            with st.container(border=True):
                st.markdown(f"**Product: {review['product_name']}**")
                st.write(f"Rating: {review['rating']} ⭐")
                st.write(f"Comment: {review['comment']}")
                st.caption(f"Reviewed on: {review['review_date']}")
                
                col_edit, col_delete = st.columns(2)
                with col_edit:
                    if st.button("Edit Review", key=f"edit_review_{review['review_id']}"):
                        st.session_state['edit_review_id'] = review['review_id']
                        st.session_state['edit_product_id'] = review['product_id']
                        st.session_state['edit_rating'] = review['rating']
                        st.session_state['edit_comment'] = review['comment']
                with col_delete:
                    if st.button("Delete Review", key=f"delete_review_{review['review_id']}"):
                        success, msg = execute_query("DELETE FROM Review WHERE review_id = %s", (review['review_id'],))
                        if success:
                            st.success("Review deleted successfully.")
                            st.rerun()
                        else:
                            st.error(f"Failed to delete review: {msg}")
            st.markdown("---")
    else:
        st.info("You have not written any reviews yet.")

    if 'edit_review_id' in st.session_state and st.session_state['edit_review_id']:
        st.subheader("Edit Your Review")
        product_name_to_edit = fetch_data("SELECT name FROM Product WHERE product_id = %s", (st.session_state['edit_product_id'],)).iloc[0]['name']
        st.write(f"Editing review for: **{product_name_to_edit}**")
        
        new_rating = st.slider("New Rating", 1, 5, st.session_state['edit_rating'], key="edit_rating_slider")
        new_comment = st.text_area("New Comment", value=st.session_state['edit_comment'], key="edit_comment_text")

        if st.button("Save Changes", key="save_review_changes"):
            success, msg = execute_query(
                "UPDATE Review SET rating = %s, comment = %s WHERE review_id = %s",
                (new_rating, new_comment, st.session_state['edit_review_id'])
            )
            if success:
                st.success("Review updated successfully.")
                del st.session_state['edit_review_id'] # Clear edit state

    st.markdown("---")
    st.subheader("Write a New Review")

    eligible_products_df = fetch_data(
        """
        SELECT DISTINCT p.product_id, p.name
        FROM Orders o
        JOIN Order_Item oi ON o.order_id = oi.order_id
        JOIN Product p ON oi.product_id = p.product_id
        LEFT JOIN Review r ON r.product_id = p.product_id AND r.customer_id = o.customer_id
        WHERE o.customer_id = %s
          AND o.status = 'delivered'
          AND r.review_id IS NULL
        ORDER BY p.name
        """,
        (user_id,)
    )

    if eligible_products_df.empty:
        st.caption("No delivered products available to review right now.")
        return

    product_options = [f"{row['product_id']} - {row['name']}" for _, row in eligible_products_df.iterrows()]
    selected_product = st.selectbox("Select a product to review", product_options, key="new_review_product")

    if selected_product:
        selected_product_id = int(selected_product.split(" - ")[0])
        rating = st.slider("Rating", 1, 5, 5, key="new_review_rating")
        comment = st.text_area("Comment", key="new_review_comment")

        if st.button("Submit Review", key="submit_new_review"):
            success, msg = execute_query(
                "INSERT INTO Review (product_id, customer_id, rating, comment) VALUES (%s, %s, %s, %s)",
                (selected_product_id, user_id, rating, comment)
            )
            if success:
                st.success("Review submitted successfully.")
                st.rerun()
            else:
                st.error(f"Failed to submit review: {msg}")

def customer_profile_page():
    st.subheader("My Profile")
    user_id = st.session_state['user_id']

    profile_df = fetch_data(
        "SELECT name, email, phone, city, state, pin, address FROM Customer WHERE customer_id = %s",
        (user_id,)
    )

    if profile_df.empty:
        st.error("Profile not found.")
        return

    data = profile_df.iloc[0]

    with st.form("profile_form"):
        name = st.text_input("Full Name", value=data['name'])
        email = st.text_input("Email", value=data['email'], disabled=True)
        phone = st.text_input("Phone", value=str(data['phone']) if data.get('phone') is not None else "")
        city = st.text_input("City", value=data['city'] if data.get('city') is not None else "")
        state = st.text_input("State", value=data['state'] if data.get('state') is not None else "")
        pin = st.text_input("PIN Code", value=str(data['pin']) if data.get('pin') is not None else "")
        address = st.text_area("Address", value=data['address'] if data.get('address') is not None else "")

        submitted = st.form_submit_button("Save Changes")

        if submitted:
            success, msg = execute_query(
                "UPDATE Customer SET name = %s, phone = %s, city = %s, state = %s, pin = %s, address = %s WHERE customer_id = %s",
                (name, phone, city, state, pin, address, user_id)
            )
            if success:
                st.success("Profile updated.")
                st.session_state['user_name'] = name
            else:
                st.error(f"Failed to update profile: {msg}")