# app.py
import streamlit as st
import pandas as pd
import plotly.express as px

# --- Authentication ---
def check_credentials(username, password):
    # Hardcoded credentials (username and password)
    correct_username = "admin"
    correct_password = "password123"  # Change to your desired password

    return username == correct_username and password == correct_password

# --- Page Config ---
st.set_page_config(
    page_title="Sales Analytics",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Load custom CSS ---
with open("styles.css") as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# --- Session Check (Login) ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False  # Ensure session is not logged in initially

# --- Login Flow ---
if not st.session_state["logged_in"]:
    # If user is not logged in, show login screen
    st.title("Login to Access Dashboard")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if check_credentials(username, password):
            st.session_state["logged_in"] = True  # Update session state
            st.success("Login Successful!")
            st.rerun()  # Rerun the app to show the sidebar and dashboard
        else:
            st.error("Incorrect username or password. Please try again.")

else:
    # If user is logged in, show the sidebar and dashboard content
    # --- Sidebar Always Present ---
    st.sidebar.title("SWIFT SAMPLE DASHBOARD")
    
    menu = st.sidebar.radio(
        "Navigation", 
        ["Dashboard", "Earnings", "Products", "Analytics", "Settings"],
        label_visibility="collapsed"
    )
    st.sidebar.markdown("---")
    st.sidebar.write("👤 Karina Limon")
    st.sidebar.write("🔊")

    # --- Load data ---
    @st.cache_data
    def load_data():
        return pd.read_csv(
            "data.csv",
            parse_dates=["ORDERDATE"],
            encoding="cp1252",       # or "latin1"
            on_bad_lines="warn",     # skip malformed rows
        )

    df = load_data()

    # --- Preprocess ---
    df["Month"] = df["ORDERDATE"].dt.to_period("M").astype(str)
    df["Year"]  = df["ORDERDATE"].dt.year.astype(str)

    # KPI calculations
    total_orders      = df["ORDERNUMBER"].nunique()
    completed_orders  = df[df["STATUS"] == "Shipped"]["ORDERNUMBER"].nunique()
    pending_orders    = total_orders - completed_orders
    total_revenue     = df["SALES"].sum()
    unique_clients    = df["CUSTOMERNAME"].nunique()

    # --- Header & KPIs ---
    st.markdown("## 📊 Sales Analytics")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Orders", f"{total_orders}")
    k2.metric("Completed Orders", f"{completed_orders}")
    k3.metric("Pending Orders", f"{pending_orders}")
    k4.metric("Total Revenue", f"${total_revenue:,.0f}")

    # --- Top Row Charts ---
    row1_col1, row1_col2 = st.columns([1,2])


    # 1) Orders Received (donut by STATUS)
    fig_orders = px.pie(
        df.groupby("STATUS").size().reset_index(name="Count"),
        names="STATUS", values="Count",
        hole=0.6, title="Orders by Status"
    )
    row1_col1.plotly_chart(fig_orders, use_container_width=True)

    # 2) Clients Activity (clients per month)
    clients_month = (
        df.groupby("Month")["CUSTOMERNAME"]
          .nunique()
          .reset_index(name="Active Clients")
    )
    fig_clients = px.bar(
        clients_month, x="Month", y="Active Clients",
        title="Clients Activity", text="Active Clients"
    )
    row1_col2.plotly_chart(fig_clients, use_container_width=True)

    # --- Summary & Profit ---
    row2_col1, row2_col2 = st.columns(2)

    with row2_col1:
        st.markdown("### Summary")
        sum1, sum2, sum3 = st.columns(3)
        sum1.metric("Unique Clients", unique_clients)
        sum2.metric("Avg Deal Size", df["DEALSIZE"].value_counts(normalize=True).idxmax())
        sum3.metric("Avg Order Value", f"${(total_revenue/total_orders):.2f}")

    with row2_col2:
        st.markdown("### Total Profit Over Time")
        profit_time = df.groupby("Month")["SALES"].sum().reset_index()
        fig_profit = px.area(
            profit_time, x="Month", y="SALES",
            title="Sales Over Time"
        )
        st.plotly_chart(fig_profit, use_container_width=True)

    # --- Sales Summary & Top Clients ---
    st.markdown("---")
    r3c1, r3c2 = st.columns([2,1])

    with r3c1:
        st.markdown("#### Sales Summary by Month")
        sales_month = profit_time
        fig_sales = px.line(
            sales_month, x="Month", y="SALES",
            markers=True, title="Monthly Sales Trend"
        )
        st.plotly_chart(fig_sales, use_container_width=True)

    with r3c2:
        st.markdown("#### Top Clients")
        top_clients = (
            df.groupby("CUSTOMERNAME")["SALES"]
              .sum().reset_index()
              .sort_values("SALES", ascending=False)
              .head(5)
        )
        st.table(top_clients.style.format({"SALES":"${:,.0f}"}))

    # --- Best Sellers, Active Buyers, Satisfaction ---
    st.markdown("---")
    b1, b2, b3 = st.columns(3)

    with b1:
        st.markdown("##### Best Sellers")
        top_products = (
            df.groupby("PRODUCTCODE")["SALES"]
              .sum().reset_index()
              .sort_values("SALES", ascending=False)
              .head(5)
        )
        fig_prod = px.bar(
            top_products, x="PRODUCTCODE", y="SALES",
            title="Top Products", text="SALES"
        )
        st.plotly_chart(fig_prod, use_container_width=True)

    with b2:
        st.markdown("##### Customer Satisfaction")
        status_counts = df["STATUS"].value_counts(normalize=True).reset_index()
        status_counts.columns = ["Status","Share"]
        fig_sat = px.pie(
            status_counts, names="Status", values="Share",
            hole=0.6, title="On-Time vs. Other"
        )
        st.plotly_chart(fig_sat, use_container_width=True)

    # --- CSV Data Table at the End ---
    st.markdown("---")
    st.markdown("### View CSV Data")
    st.dataframe(df, use_container_width=True)  # Display the CSV data as a table with full width
