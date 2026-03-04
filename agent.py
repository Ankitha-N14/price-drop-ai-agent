import pandas as pd
import sqlite3
from datetime import datetime
import os
from groq import Groq

# -----------------------------
# AI analysis using Groq
# -----------------------------
def ai_analysis(product, brand, old_price, new_price):

    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    prompt = f"""
The price of {brand} {product} has dropped from ₹{old_price} to ₹{new_price}.
Should a customer buy now or wait for a better deal?
Give a short recommendation.
"""

    try:
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": prompt}],
        )

        decision = response.choices[0].message.content.strip()
        return decision

    except:
        return "Price dropped. Consider buying now."


# -----------------------------
# Insert alert into database
# -----------------------------
def insert_alert(product, brand, seller, old_price, new_price, drop, percent, decision):

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # check duplicate
    cursor.execute("""
        SELECT * FROM alerts
        WHERE product=? AND brand=? AND seller=? AND new_price=?
    """, (product, brand, seller, new_price))

    existing = cursor.fetchone()

    if existing:
        conn.close()
        return

    cursor.execute("""
        INSERT INTO alerts
        (product, brand, seller, old_price, new_price, price_drop, percent_drop, decision, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        product,
        brand,
        seller,
        int(old_price),
        int(new_price),
        int(drop),
        float(percent),
        decision,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()
    conn.close()


# -----------------------------
# Run the price monitoring agent
# -----------------------------
def run_agent():

    print("Checking prices...")

    df = pd.read_csv("prices.csv")

    # group by product + brand + seller
    groups = df.groupby(["product", "brand", "seller"])

    for (product, brand, seller), group in groups:

        prices = group["price"].tolist()

        if len(prices) < 2:
            continue

        old_price = prices[0]
        new_price = prices[-1]

        if new_price < old_price:

            drop = old_price - new_price
            percent = (drop / old_price) * 100

            decision = ai_analysis(product, brand, old_price, new_price)

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

    print("Price check completed.")


# -----------------------------
# Run script
# -----------------------------
if __name__ == "__main__":
    run_agent()
