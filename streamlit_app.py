import streamlit as st
import sqlite3
import pandas as pd
import subprocess

st.set_page_config(page_title="AI Price Drop Agent", layout="wide")

st.title("Autonomous AI Price Monitoring Agent")

st.write("Track any product and detect price drops automatically.")

# ==============================
# User Input Section
# ==============================

st.subheader("Track a Product")

product = st.text_input("Enter Product Name")

category = st.selectbox(
    "Select Category",
    ["Electronics", "Fashion", "Home Appliances", "Books", "Accessories", "Other"]
)

site = st.selectbox(
    "Select Website",
    ["Amazon", "Flipkart"]
)

if st.button("Check Price"):

    if product == "":
        st.warning("Please enter a product name.")

    else:

        command = f'python agent.py "{product}" "{site}"'
        subprocess.run(command, shell=True)

        st.success("Agent executed successfully!")

# ==============================
# Display Alerts
# ==============================

st.subheader("Detected Price Drops")

conn = sqlite3.connect("database.db")

df = pd.read_sql_query(
    "SELECT * FROM alerts ORDER BY id DESC",
    conn
)

conn.close()

if len(df) > 0:

    st.dataframe(
        df,
        use_container_width=True
    )

else:

    st.info("No price drops detected yet.")
