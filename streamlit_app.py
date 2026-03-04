import streamlit as st
import sqlite3
import pandas as pd

st.set_page_config(page_title="AI Price Drop Dashboard", layout="wide")

st.title("AI Price Drop Dashboard")

conn = sqlite3.connect("database.db")

try:
    df = pd.read_sql("SELECT * FROM alerts ORDER BY id DESC", conn)

    if len(df) == 0:
        st.warning("No alerts found yet.")
    else:
        st.dataframe(df, use_container_width=True)

except:
    st.error("Database not initialized. Run agent.py first.")

conn.close()
