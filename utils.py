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
    cursor = get_cursor()
    try:
        cursor.execute(query, _normalize_params(params))
        data = cursor.fetchall()
        return pd.DataFrame(data) if data else pd.DataFrame()
    except mysql.connector.Error as err:
        st.error(f"Database error: {err}")
        return pd.DataFrame()
    finally:
        cursor.close()

def execute_query(query, params=None):
    """Executes an INSERT, UPDATE, or DELETE query."""
    conn = get_connection()
    cursor = get_cursor()
    try:
        cursor.execute(query, _normalize_params(params))
        conn.commit()
        return True, "Operation successful."
    except mysql.connector.Error as err:
        conn.rollback()
        return False, f"Operation failed: {err}"
    finally:
        cursor.close()

def call_procedure(procedure_name, params=None):
    """Calls a stored procedure."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True) # Ensure dictionary output for procedures
    try:
        if params:
            cursor.callproc(procedure_name, _normalize_params(params))
        else:
            cursor.callproc(procedure_name)
        
        # Fetch results from procedure calls if any
        results = []
        for result in cursor.stored_results():
            results.extend(result.fetchall())
        
        conn.commit()
        return True, results
    except mysql.connector.Error as err:
        conn.rollback()
        return False, f"Procedure call failed: {err}"
    finally:
        cursor.close()

def get_product_details(product_id):
    """Fetches details for a single product."""
    return fetch_data("SELECT * FROM Product WHERE product_id = %s", (product_id,))

def display_product_card(product_data):
    """Displays a single product as a card."""
    with st.container(border=True):
        col1, col2 = st.columns([1, 3])
        with col1:
            # Use a placeholder image if image_url is not set or invalid
            original_image = product_data.get('image_url')
            image_src = original_image if original_image else None
            if isinstance(image_src, str):
                is_web = image_src.startswith("http://") or image_src.startswith("https://")
                is_file = os.path.exists(image_src)
                if not (is_web or is_file):
                    # Try resolving against common local asset folders if it's a bare filename
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

            _placeholder_png = base64.b64decode(
                "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGMAAQAABQABDQottQAAAABJRU5ErkJggg=="
            )
            try:
                if image_src:
                    st.image(image_src, width=100)
                else:
                    st.image(_placeholder_png, width=100)
            except Exception:
                st.image(_placeholder_png, width=100)
            # Optional debug of resolved image path/url
            if st.session_state.get('debug_images'):
                st.caption(f"base_dir: {os.path.dirname(__file__)}")
                st.caption(f"cwd: {os.getcwd()}")
                st.caption(f"image(raw): {original_image}")
                st.caption(f"image(resolved): {image_src if image_src else 'placeholder-bytes'}")
                # Show candidate paths and whether they exist
                try:
                    if isinstance(original_image, str) and not (original_image.startswith('http://') or original_image.startswith('https://') or os.path.exists(original_image)):
                        _cands = [
                            os.path.join(os.path.dirname(__file__), "images", original_image),
                            os.path.join(os.path.dirname(__file__), "assets", original_image),
                            os.path.join(os.path.dirname(__file__), "assets", "images", original_image),
                            os.path.join(os.path.dirname(__file__), "PICTURES", original_image),
                            os.path.join(os.getcwd(), "images", original_image),
                            os.path.join(os.getcwd(), "assets", original_image),
                            os.path.join(os.getcwd(), "assets", "images", original_image),
                            os.path.join(os.getcwd(), "PICTURES", original_image),
                        ]
                        st.caption("candidates:")
                        for p in _cands:
                            st.caption(f" - {p} :: {'OK' if os.path.exists(p) else 'missing'}")
                except Exception:
                    pass
        with col2:
            st.markdown(f"**{product_data['name']}**")
            st.write(f"₹{product_data['price']:.2f}")
            if product_data.get('average_rating') is not None:
                st.caption(f"Rating: {product_data['average_rating']:.2f} ⭐")
            else:
                st.caption("No reviews yet")
            st.caption(f"Stock: {product_data['stock_quantity']}")
            if product_data['stock_quantity'] == 0:
                st.info("Out of Stock")

def display_order_item_card(item_data):
    """Displays a single order item."""
    with st.container(border=True):
        st.markdown(f"**Product: {item_data['product_name']}**")
        st.write(f"Quantity: {item_data['quantity']}")
        st.write(f"Price at Purchase: ₹{item_data['price_at_purchase']:.2f}")
        st.write(f"Subtotal: ₹{item_data['subtotal']:.2f}")

def apply_custom_css():
    """Applies custom CSS for better UI."""
    st.markdown("""
        <style>
        /* General Streamlit container padding adjustment */
        .st-emotion-cache-1r6dm7m {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        .st-emotion-cache-z5fcl4 {
            padding-top: 1rem;
            padding-bottom: 1rem;
        }
        /* Columns spacing */
        .st-emotion-cache-1av49rkb {
            gap: 1rem;
        }
        /* Buttons styling */
        .stButton button {
            background-color: #4CAF50;
            color: white;
            padding: 8px 16px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            width: 100%; /* Make buttons fill their column */
            margin-bottom: 5px; /* Add some space between buttons */
        }
        .stButton button:hover {
            background-color: #45a049;
        }
        /* Number input adjustments */
        .css-1cpxqw2 e1ju4r1p0 { /* Target for specific number input component */
            margin-top: -10px;
        }
        /* Tabs styling */
        .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
            font-size: 1.2rem; /* Larger font for tab titles */
        }
        .stTabs [data-baseweb="tab"] {
            font-size: 1.1rem;
            padding: 10px 15px;
        }
        .stTabs [aria-selected="true"] {
            border-bottom-color: #4CAF50 !important; /* Active tab indicator color */
            color: #4CAF50 !important; /* Active tab text color */
        }

        /* Product card styling */
        .st-emotion-cache-1ekfihx { /* This is a common class for st.container, may need adjustment */
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            transition: 0.3s;
            padding: 15px;
            margin-bottom: 15px;
        }
        .st-emotion-cache-1ekfihx:hover {
            box-shadow: 0 8px 16px rgba(0,0,0,0.2);
        }
        </style>
        """, unsafe_allow_html=True)

# New function to fetch categories
def get_categories():
    return fetch_data("SELECT category_id, category_name FROM Category ORDER BY category_name")