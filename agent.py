import pandas as pd
import sqlite3
from datetime import datetime

# ==============================
# Create database table
# ==============================
def create_table():

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product TEXT,
        brand TEXT,
        seller TEXT,
        old_price INTEGER,
        new_price INTEGER,
        price_drop INTEGER,
        percent_drop REAL,
        decision TEXT,
        timestamp TEXT
    )
    """)

    conn.commit()
    conn.close()


# ==============================
# Insert alert into database
# ==============================
def insert_alert(product, brand, seller, old_price, new_price, drop, percent, decision):

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO alerts
    (product, brand, seller, old_price, new_price, price_drop, percent_drop, decision, timestamp)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        product,
        brand,
        seller,
        old_price,
        new_price,
        drop,
        percent,
        decision,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()
    conn.close()


# ==============================
# AI decision logic
# ==============================
def generate_decision(product, brand, drop, percent):

    if percent >= 10:
        decision = "BUY NOW: Price of " + brand + " " + product + " dropped by Rs " + str(drop)

    elif percent >= 5:
        decision = "Good deal: Price dropped by Rs " + str(drop)

    else:
        decision = "Minor price drop detected"

    return decision


# ==============================
# Run agent
# ==============================
def run_agent():

    print("Checking prices...")

    create_table()

    df = pd.read_csv("prices.csv")

    grouped = df.groupby(["product", "brand", "seller"])

    for (product, brand, seller), group in grouped:

        prices = group["price"].tolist()

        if len(prices) < 2:
            continue

        old_price = prices[0]
        new_price = prices[-1]

        if new_price < old_price:

            drop = old_price - new_price
            percent = (drop / old_price) * 100

            decision = generate_decision(product, brand, drop, percent)

            insert_alert(
                product,
                brand,
                seller,
                old_price,
                new_price,
                drop,
                percent,
                decision
            )

            print("Price drop detected for", product, "(" + brand + ")")


# ==============================
# Start agent
# ==============================
if __name__ == "__main__":
    run_agent()
