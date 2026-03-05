import streamlit as st
import pandas as pd
import sqlite3

# -----------------------------
# Page Config
# -----------------------------

st.set_page_config(
    page_title="AI Price Drop Dashboard",
    layout="wide"
)

st.title("AI Price Drop Dashboard")

# -----------------------------
# Connect to database
# -----------------------------

conn = sqlite3.connect("database.db")

# Get latest alerts
df = pd.read_sql_query(
    "SELECT * FROM alerts ORDER BY id DESC LIMIT 20",
    conn
)

conn.close()

# -----------------------------
# Metrics Section
# -----------------------------

if not df.empty:

    col1, col2, col3 = st.columns(3)

    col1.metric("Total Alerts", len(df))
    col2.metric("Largest Drop ₹", int(df["price_drop"].max()))
    col3.metric("Best Drop %", round(df["percent_drop"].max(), 2))

else:

    st.warning("No alerts detected yet.")

# -----------------------------
# Highlight deals
# -----------------------------

def highlight_deals(row):

    if row["percent_drop"] >= 10:
        return ["background-color: #1f8b4c"] * len(row)

    elif row["percent_drop"] >= 5:
        return ["background-color: #b88900"] * len(row)

    return [""] * len(row)


# -----------------------------
# Display Table
# -----------------------------

if not df.empty:

    styled_df = df.style.apply(highlight_deals, axis=1)

    st.dataframe(
        styled_df,
        use_container_width=True
    )

else:

    st.write("Run the agent to generate alerts.")

# -----------------------------
# Footer
# -----------------------------

st.markdown("---")

st.caption(
    "Autonomous AI Agent for Price Monitoring • Web Scraping • AI Decision Logic • Email Alerts"
)
