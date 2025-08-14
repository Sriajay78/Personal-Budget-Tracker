import streamlit as st
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
from datetime import date

DB_NAME = "budget.db"

# ---------- DB Helpers ----------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    type TEXT,
                    category TEXT,
                    amount REAL,
                    description TEXT
                )''')
    conn.commit()
    conn.close()

def add_transaction(date, t_type, category, amount, description):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO transactions (date, type, category, amount, description) VALUES (?, ?, ?, ?, ?)",
              (date, t_type, category, amount, description))
    conn.commit()
    conn.close()

def fetch_transactions():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM transactions", conn)
    conn.close()
    return df

# ---------- App ----------
st.set_page_config(page_title="Budget Tracker", page_icon="💰", layout="wide")
st.title("💰 Personal Budget Tracker")
init_db()

# Sidebar - Add Transaction
st.sidebar.header("Add Transaction")
t_date = st.sidebar.date_input("Date", date.today())
t_type = st.sidebar.selectbox("Type", ["Income", "Expense"])
t_category = st.sidebar.text_input("Category")
t_amount = st.sidebar.number_input("Amount", min_value=0.0, format="%.2f")
t_description = st.sidebar.text_input("Description")
if st.sidebar.button("Add"):
    if t_category and t_amount > 0:
        add_transaction(str(t_date), t_type, t_category, t_amount, t_description)
        st.sidebar.success("Transaction added!")
    else:
        st.sidebar.error("Please enter category and amount.")

# Main View
df = fetch_transactions()

if df.empty:
    st.info("No transactions yet. Add some from the sidebar.")
else:
    df["date"] = pd.to_datetime(df["date"])
    
    # Filters
    st.subheader("Filters")
    col1, col2, col3 = st.columns(3)
    with col1:
        start_date = st.date_input("Start Date", df["date"].min().date())
    with col2:
        end_date = st.date_input("End Date", df["date"].max().date())
    with col3:
        category_filter = st.multiselect("Category", df["category"].unique())

    filtered = df[
        (df["date"] >= pd.to_datetime(start_date)) &
        (df["date"] <= pd.to_datetime(end_date))
    ]
    if category_filter:
        filtered = filtered[filtered["category"].isin(category_filter)]

    # Table
    st.subheader("Transactions")
    st.dataframe(filtered.sort_values("date", ascending=False), use_container_width=True)

    # KPIs
    total_income = filtered.loc[filtered["type"] == "Income", "amount"].sum()
    total_expense = filtered.loc[filtered["type"] == "Expense", "amount"].sum()
    balance = total_income - total_expense

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Income", f"₹{total_income:,.2f}")
    c2.metric("Total Expense", f"₹{total_expense:,.2f}")
    c3.metric("Balance", f"₹{balance:,.2f}")

    # Charts
    st.subheader("Visualizations")
    col_a, col_b = st.columns(2)

    # Pie Chart - Expenses by Category
    with col_a:
        exp_data = filtered[filtered["type"] == "Expense"]
        if not exp_data.empty:
            cat_sum = exp_data.groupby("category")["amount"].sum()
            fig1, ax1 = plt.subplots()
            ax1.pie(cat_sum, labels=cat_sum.index, autopct="%1.1f%%", startangle=90)
            ax1.axis("equal")
            st.pyplot(fig1)
        else:
            st.info("No expense data for pie chart.")

    # Bar Chart - Income vs Expense over time
    with col_b:
        daily_sum = filtered.groupby(["date", "type"])["amount"].sum().unstack(fill_value=0)
        fig2, ax2 = plt.subplots()
        daily_sum.plot(kind="bar", stacked=True, ax=ax2)
        ax2.set_ylabel("Amount")
        ax2.set_title("Income vs Expense Over Time")
        st.pyplot(fig2)

    # Download Option
    st.download_button(
        "Download Transactions CSV",
        filtered.to_csv(index=False).encode("utf-8"),
        file_name="transactions.csv",
        mime="text/csv"
    )

st.caption("Data is stored locally in 'budget.db'. No uploads required.")
