import os
import time
import threading
import pandas as pd
import sqlite3
from datetime import datetime
from flask import Flask, render_template
from groq import Groq
from notifier import send_email

app = Flask(__name__)


# ---------------- AI Analysis ---------------- #

def ai_analysis(product, brand, seller, old_price, new_price):
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    prompt = f"""
    Product: {product}
    Brand: {brand}
    Seller: {seller}
    Old Price: Rs {old_price}
    New Price: Rs {new_price}

    Should the user BUY now or WAIT?
    Give short reasoning in 2 lines.
    """

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content


# ---------------- Database ---------------- #

def save_to_db(product, brand, seller, old_price, new_price, price_drop, percent, decision):
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
        price_drop,
        percent,
        decision,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()
    conn.close()


def run_agent():
    print("Checking prices...")

    df = pd.read_csv("prices.csv")
    grouped = df.groupby(["product", "brand", "seller"])

    for (product, brand, seller), group in grouped:

        if len(group) < 2:
            continue

        old_price = int(group.iloc[-2]["price"])
        new_price = int(group.iloc[-1]["price"])

        if new_price < old_price:
            price_drop = old_price - new_price
            percent = round((price_drop / old_price) * 100, 2)

            decision = ai_analysis(product, brand, seller, old_price, new_price)

            save_to_db(product, brand, seller, old_price, new_price, price_drop, percent, decision)

            send_email(
                "Price Drop Alert!",
                f"{product} dropped from Rs {old_price} to Rs {new_price}"
            )

    print("Check complete.")


# ---------------- Background Scheduler ---------------- #

def scheduler():
    while True:
        run_agent()
        time.sleep(300)  # 5 minutes


threading.Thread(target=scheduler, daemon=True).start()


# ---------------- Dashboard ---------------- #

@app.route("/")
def home():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM alerts ORDER BY id DESC")
    alerts = cursor.fetchall()

    conn.close()

    return render_template("index.html", alerts=alerts)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
