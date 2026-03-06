import streamlit as st
import sqlite3
import pandas as pd
import subprocess

st.title("AI Price Drop Agent")

st.subheader("Track a Product")

product = st.text_input("Enter product name")

site = st.selectbox(
    "Select website",
    ["Amazon", "Flipkart"]
)

if st.button("Track Price"):

    command = f"python agent.py '{product}' '{site}'"
    subprocess.run(command, shell=True)

    st.success("Agent executed! Checking price...")

# ==============================
# Show Alerts
# ==============================

conn = sqlite3.connect("database.db")

df = pd.read_sql_query(
    "SELECT * FROM alerts ORDER BY id DESC",
    conn
)

conn.close()

st.subheader("Price Drop Alerts")

st.dataframe(df)
