import streamlit as st
import sqlite3
import pandas as pd

st.set_page_config(page_title="AI Price Drop Dashboard", layout="wide")

st.title("AI Price Drop Dashboard")

# connect to database
conn = sqlite3.connect("database.db")

query = "SELECT * FROM alerts ORDER BY id DESC"

try:
    df = pd.read_sql(query, conn)

    if df.empty:
        st.warning("No alerts yet")
    else:
        st.dataframe(df, use_container_width=True)

except:
    st.error("Database not initialized yet. Run agent first.")

conn.close()
