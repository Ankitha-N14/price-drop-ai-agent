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
        str(product),
        str(brand),
        str(seller),
        int(old_price),
        int(new_price),
        int(drop),
        float(percent),
        str(decision),
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()
    conn.close()


# ==============================
# AI Decision Logic
# ==============================
def generate_decision(product, brand, drop, percent):

    if percent >= 10:
        return f"You should BUY now as the price of the {brand} {product} has dropped by Rs {drop}"

    elif percent >= 5:
        return f"Price dropped by Rs {drop}. Consider buying soon."

    else:
        return "Price drop detected but waiting for a better deal."


# ==============================
# Run the price monitoring agent
# ==============================
def run_agent():

    print("Checking prices...")

    # Ensure database exists
    create_table()

    # Load price data
    df = pd.read_csv("prices.csv")

    # Group by product + brand + seller
    groups = df.groupby(["product", "brand", "seller"])

    for (product, brand, seller), group in groups:

        prices = group["price"].tolist()

        # Need at least 2 prices to compare
        if len(prices) < 2:
            continue

        old_price = prices[0]
        new_price = prices[-1]

        # Check if price dropped
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

            print(f"Price drop detected for {product} ({brand})")


# ==============================
# Run script
# ==============================
if __name__ == "__main__":
    run_agent()
