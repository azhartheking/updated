import streamlit as st
import pandas as pd
import openpyxl 
from openpyxl.chart import BarChart, Reference
from openpyxl.drawing.image import Image
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import time
import os
import altair as alt

# File paths
ORDER_HISTORY_FILE = 'order_history.csv'
LOYALTY_POINTS_FILE = 'loyalty_points.csv'
RATINGS_FILE = 'ratings.csv'
USERS_FILE = 'users.csv'

# Initialize data (mock data for menu and inventory)
menu = {
    "Americano": 5.00,
    "Cappuccino": 6.00,
    "Latte": 6.50,
    "Caramel Macchiato": 7.00
}

default_inventory = {
    "coffee_beans": 1000,  # grams
    "milk": 500,           # ml
    "sugar": 200,          # grams
    "cups": 100            # count
}

# Initialize session state for order history, inventory, login status, loyalty points, and ratings
if "order_history" not in st.session_state:
    if os.path.exists(ORDER_HISTORY_FILE):
        st.session_state["order_history"] = pd.read_csv(ORDER_HISTORY_FILE).to_dict(orient='records')
    else:
        st.session_state["order_history"] = []

if "inventory" not in st.session_state:
    st.session_state["inventory"] = default_inventory.copy()

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if "user_role" not in st.session_state:
    st.session_state["user_role"] = None

if "loyalty_points" not in st.session_state:
    if os.path.exists(LOYALTY_POINTS_FILE):
        st.session_state["loyalty_points"] = pd.read_csv(LOYALTY_POINTS_FILE, index_col=0).to_dict()['Points']
    else:
        st.session_state["loyalty_points"] = {}

if "ratings" not in st.session_state:
    if os.path.exists(RATINGS_FILE):
        st.session_state["ratings"] = pd.read_csv(RATINGS_FILE).to_dict(orient='records')
    else:
        st.session_state["ratings"] = []

if "current_order" not in st.session_state:
    st.session_state["current_order"] = None

if "rating_submitted" not in st.session_state:
    st.session_state["rating_submitted"] = False

if "show_register_form" not in st.session_state:
    st.session_state["show_register_form"] = False

if "show_login_form" not in st.session_state:
    st.session_state["show_login_form"] = False

if "show_admin_login_form" not in st.session_state:
    st.session_state["show_admin_login_form"] = False

# Function to save order history to CSV
def save_order_history():
    pd.DataFrame(st.session_state["order_history"]).to_csv(ORDER_HISTORY_FILE, index=False)

# Function to save loyalty points to CSV
def save_loyalty_points():
    pd.DataFrame(list(st.session_state["loyalty_points"].items()), columns=["Customer", "Points"]).to_csv(LOYALTY_POINTS_FILE, index=False)

# Function to save ratings to CSV
def save_ratings():
    pd.DataFrame(st.session_state["ratings"]).to_csv(RATINGS_FILE, index=False)

# Function to save users to CSV
def save_users(users_df):
    users_df.to_csv(USERS_FILE, index=False)

# Load users from CSV
def load_users():
    if os.path.exists(USERS_FILE):
        return pd.read_csv(USERS_FILE)
    else:
        return pd.DataFrame(columns=["username", "password"])

# Function to generate an invoice
def generate_invoice(order):
    return f"""
    Invoice
    ---------
    Customer Name: {order['customer_name']}
    Coffee Type: {order['coffee_type']}
    Size: {order['size']}
    Add-ons: {', '.join(order['add_ons']) if order['add_ons'] else 'None'}
    Total Price: ${order['price']:.2f}
    Order Time: {order['order_time']}
    """

# Function to add loyalty points
def add_loyalty_points(customer_name, points):
    if customer_name in st.session_state["loyalty_points"]:
        st.session_state["loyalty_points"][customer_name] += points
    else:
        st.session_state["loyalty_points"][customer_name] = points
    save_loyalty_points()

# Registration form
if st.sidebar.button("Register New User"):
    st.session_state["show_register_form"] = not st.session_state["show_register_form"]

if st.session_state["show_register_form"]:
    with st.sidebar.form(key="register_form"):
        st.subheader("Register New User")
        new_username = st.text_input("Enter Username", key="register_username")
        new_password = st.text_input("Enter Password", type="password", key="register_password")
        register_button = st.form_submit_button("Register")
        if register_button:
            users_df = load_users()
            if new_username in users_df["username"].values:
                st.sidebar.error("Username already exists. Please choose a different username.")
            else:
                new_user = pd.DataFrame([[new_username, new_password]], columns=["username", "password"])
                users_df = pd.concat([users_df, new_user], ignore_index=True)
                save_users(users_df)
                st.sidebar.success("Registration successful. You can now log in.")
                st.session_state["show_register_form"] = False

# Login form
if st.sidebar.button("Login"):
    st.session_state["show_login_form"] = not st.session_state["show_login_form"]

if st.session_state["show_login_form"]:
    with st.sidebar.form(key="login_form"):
        st.subheader("Login")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        login_button = st.form_submit_button("Login")
        if login_button:
            users_df = load_users()
            if username in users_df["username"].values:
                stored_password = users_df[users_df["username"] == username]["password"].values[0]
                if password == stored_password:
                    st.session_state["logged_in"] = True
                    st.session_state["user_role"] = "customer"
                    st.session_state["username"] = username
                    st.sidebar.success("Login successful.")
                    st.session_state["show_login_form"] = False
                else:
                    st.sidebar.error("Incorrect password. Please try again.")
            else:
                st.sidebar.error("Username not found. Please register first.")

# Admin login form
if st.sidebar.button("Admin"):
    st.session_state["show_admin_login_form"] = not st.session_state["show_admin_login_form"]

if st.session_state["show_admin_login_form"]:
    with st.sidebar.form(key="admin_login_form"):
        st.subheader("Admin Login")
        username = st.text_input("Username", key="admin_username")
        password = st.text_input("Password", type="password", key="admin_password")
        admin_login_button = st.form_submit_button("Login as Admin")
        if admin_login_button:
            if username == "admin" and password == "admin123":
                st.session_state["logged_in"] = True
                st.session_state["user_role"] = "admin"
                st.sidebar.success("Admin Access Granted")
                st.session_state["show_admin_login_form"] = False
            else:
                st.sidebar.error("Invalid admin credentials.")
                st.session_state["is_admin"] = False  # Reset admin flag if login fails

# App title
st.sidebar.title("BrewMate App Navigation")

# Sidebar for navigation
if st.session_state["logged_in"] and st.session_state["user_role"] == "admin":
    page = st.sidebar.radio("Go to", ("Home",'Order Now', "About Us", "Contact Us", "Admin Panel"))
else:
    page = st.sidebar.radio("Go to", ("Home",'Order Now', "About Us", "Contact Us"))

# Display appropriate page based on selection
if page == "Home":
    st.title("Welcome to BrewMate!")
    st.subheader("Exclusive Promotions and Benefits!")
    st.image("https://images.unsplash.com/photo-1511920170033-f8396924c348", use_column_width=True)
    promotions = ["**Enjoy 10% off on your first order, earn loyalty points for every dollar spent, get exclusive member promotions, a free birthday coffee, and priority customer support!**"]
    for promotion in promotions:
        st.markdown(promotion)
    st.write("Click below to join our membership and start enjoying the benefits!")
    if st.button("Join Now"):
        st.success("Thank you for joining! You are now a valued member of our coffee shop family.")

elif page == 'Order Now':
    # Display Order Site
    if st.session_state['logged_in'] and st.session_state["user_role"] == "customer" :
        # Customer Order Process
        st.subheader("Place Your Order")
        customer_name = st.session_state["username"]
        coffee_type = st.selectbox("Select Coffee Type", list(menu.keys()))
        coffee_size = st.radio("Choose Size", ("Small", "Medium", "Large"))
        add_ons = st.multiselect("Add-ons", ["Extra sugar", "Milk"])

        # Calculate Total Price
        base_price = menu[coffee_type]
        total_price = base_price
        if coffee_size == "Medium":
            total_price += 1.00
        elif coffee_size == "Large":
            total_price += 2.00
        if "Extra sugar" in add_ons:
            total_price += 0.50
        if "Milk" in add_ons:
            total_price += 0.75

        st.write(f"Total Price: ${total_price:.2f}")

        # Payment Integration before Order Placement
        st.subheader("Payment Integration")
        payment_method = st.selectbox("Choose Payment Method", ["Credit Card", "PayPal"])
        if st.button("Confirm Payment"):
            st.success("Payment successful!")
            order = {
                "customer_name": customer_name,
                "coffee_type": coffee_type,
                "size": coffee_size,
                "add_ons": add_ons,
                "price": total_price,
                "order_time": datetime.now()
            }
            st.session_state["current_order"] = order
            st.session_state["order_history"].append(order)
            save_order_history()
            st.success(f"Order placed! Your coffee will be ready shortly. Order: {coffee_type} ({coffee_size})")

            # Display the generated invoice and provide download option
            st.subheader("Invoice")
            invoice_text = generate_invoice(order)
            st.text(invoice_text)
            st.download_button(label="Download Invoice", data=invoice_text, file_name=f"invoice_{customer_name}.txt", mime="text/plain")

            # Add loyalty points (e.g., 1 point per $1 spent)
            points_earned = int(order["price"])
            add_loyalty_points(customer_name, points_earned)
            st.info(f"{points_earned} loyalty points added. Total points: {st.session_state['loyalty_points'].get(customer_name, 0)}")

            # Update Inventory based on order (basic example)
            st.session_state["inventory"]["coffee_beans"] -= 10  # Adjust amount as per recipe
            st.session_state["inventory"]["cups"] -= 1

            # Start countdown for order preparation
            for i in range(5, 0, -1):
                st.info(f"Your order will be ready in {i} seconds...")
                time.sleep(1)
            st.success(f"{st.session_state['current_order']['customer_name']}, your {st.session_state['current_order']['coffee_type']} is ready!")

            # Set rating submission flag to False for new rating submission
            st.session_state["rating_submitted"] = False

        # Collect customer rating and feedback after the coffee is ready
        if st.session_state["current_order"] and not st.session_state["rating_submitted"]:
            st.subheader("Rate Your Experience")
            rating = st.slider("Rate your coffee (1-5)", min_value=1, max_value=5, key="rating_slider")
            feedback = st.text_area("Leave your feedback", key="feedback_area")
            if st.button("Submit Rating"):
                st.session_state["ratings"].append({"Customer": customer_name, "Rating": rating, "Feedback": feedback})
                save_ratings()
                st.success("Thank you for your feedback!")
                st.session_state["rating_submitted"] = True
    else:
        st.text('Access Denied. Please log in to place an order.')
            

elif page == 'About Us':
    # Display Groupmates Names and etc
    st.title("About BrewMate")
    st.write("BrewMate is a coffee shop dedicated to providing the best coffee experience. We offer a variety of handcrafted beverages, each made with care and passion. Our goal is to create a welcoming environment for all our customers, where great coffee and community come together.")
    # Team pictures
    col1, col2, col3 = st.columns(3)
    with col1:
        st.image('azhar.jpg', caption='Azhar Ali, Founder', use_column_width=True)
    with col2:
        st.image('ad.jpg', caption='Adrish Elnes, Co-Founder', use_column_width=True)
    with col3:
        st.image('bolo.jpg', caption='Nabilah Shamshir, Accountant', use_column_width=True)
    col4, col5 = st.columns(2)
    with col4:
        st.image('vv.jpg', caption='Vivian Hwong, Manager', use_column_width=True)
    with col5:
        st.image('dio.jpg', caption='Diocleciana, Executive Chef', use_column_width=True)

elif page == 'Contact Us':
    st.title('Contact Us')
    st.subheader('Our contact information')
    st.text('Email us at Azhario123@gmail.com')

elif page == "Admin Panel" and st.session_state["logged_in"] and st.session_state["user_role"] == "admin":
    st.title("Admin Panel")
    st.subheader("Inventory Management")
    # Display current inventory levels
    st.write("Inventory Levels")
    for item, qty in st.session_state["inventory"].items():
        st.write(f"{item.capitalize()}: {qty} units")

    # Low stock alert
    for item, qty in st.session_state["inventory"].items():
        if qty < 20:
            st.warning(f"Low stock alert: {item}")

    # Update inventory
    item_to_restock = st.selectbox("Item to Restock", list(st.session_state["inventory"].keys()))
    restock_amount = st.number_input("Restock Amount", min_value=1)
    if st.button("Restock Inventory"):
        st.session_state["inventory"][item_to_restock] += restock_amount
        st.success(f"{item_to_restock.capitalize()} restocked successfully.")

    # Sales Reporting
    st.subheader("Sales Reporting")
    if st.session_state["order_history"]:
        sales_df = pd.DataFrame(st.session_state["order_history"])
        st.write("Total Sales Data")
        st.dataframe(sales_df)

        # Sales Breakdown by Coffee Type
        sales_summary = sales_df["coffee_type"].value_counts()
        st.bar_chart(sales_summary, use_container_width=True)

        # Total Profit Calculation (mock example)
        total_sales = sum(order["price"] for order in st.session_state["order_history"])
        st.write(f"Total Revenue: ${total_sales}")

        # Daily, Weekly, and Monthly Profit Calculation with Graphs
        today = datetime.now()
        sales_df['order_time'] = pd.to_datetime(sales_df['order_time'])

        daily_sales = sales_df[sales_df['order_time'] >= (today - timedelta(days=1))]
        weekly_sales = sales_df[sales_df['order_time'] >= (today - timedelta(weeks=1))]
        monthly_sales = sales_df[sales_df['order_time'] >= (today - timedelta(days=30))]

        daily_profit = daily_sales['price'].sum()
        weekly_profit = weekly_sales['price'].sum()
        monthly_profit = monthly_sales['price'].sum()

        profit_data = pd.DataFrame({
            'Period': ['Daily', 'Weekly', 'Monthly'],
            'Profit': [daily_profit, weekly_profit, monthly_profit]
        })
        st.write(f"Daily Profit: ${daily_profit:.2f}")
        st.write(f"Weekly Profit: ${weekly_profit:.2f}")
        st.write(f"Monthly Profit: ${monthly_profit:.2f}")
        st.bar_chart(profit_data.set_index('Period'), use_container_width=True)

        # Least and Best Selling Product
        st.subheader("Product Performance")
        best_selling = sales_summary.idxmax()
        least_selling = sales_summary.idxmin()
        st.write(f"Best Selling Product: {best_selling}")
        st.write(f"Least Selling Product: {least_selling}")
        st.bar_chart(sales_summary, use_container_width=True)

    # Display loyalty points summary
    st.subheader("Loyalty Points Summary")
    loyalty_points_df = pd.DataFrame(st.session_state["loyalty_points"].items(), columns=["Customer", "Points"])
    st.dataframe(loyalty_points_df)

    # Display ratings summary
    st.subheader("Ratings Summary")
    if st.session_state["ratings"]:
        ratings_df = pd.DataFrame(st.session_state["ratings"], columns=["Customer", "Rating", "Feedback"])
        st.dataframe(ratings_df)
        avg_rating = ratings_df["Rating"].mean()
        st.write(f"Average Rating: {avg_rating:.2f} / 5")
