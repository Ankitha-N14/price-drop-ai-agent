# -*- coding: utf-8 -*-

import pandas as pd
import sqlite3
from datetime import datetime
from notifier import send_email
from groq import Groq
import os


def ai_analysis(product, brand, seller, old_price, new_price):
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    prompt = (
        "Product: " + product + "\n"
        "Brand: " + brand + "\n"
        "Seller: " + seller + "\n"
        "Old Price: Rs " + str(old_price) + "\n"
        "New Price: Rs " + str(new_price) + "\n\n"
        "Should the user BUY now or WAIT?\n"
        "Give short reasoning in 2 lines."
    )

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",   # updated working model
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content


def save_to_db(product, brand, seller, old_price, new_price, drop, percent, decision):
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


def run_agent():
    df = pd.read_csv("prices.csv")

    grouped = df.groupby(["product", "brand", "seller"])

    alerts_generated = False

    for (product, brand, seller), group in grouped:

        if len(group) < 2:
            continue

        old_price = int(group.iloc[-2]["price"])
        new_price = int(group.iloc[-1]["price"])

        if new_price < old_price:

            drop = int(old_price - new_price)
            percent = round((drop / old_price) * 100, 2)

            decision = ai_analysis(
                product,
                brand,
                seller,
                old_price,
                new_price
            )

            save_to_db(
                product,
                brand,
                seller,
                old_price,
                new_price,
                drop,
                percent,
                decision
            )

            alerts_generated = True

    if alerts_generated:
        send_email(
            "Price Drop Detected Across Sellers!",
            "Check your dashboard for full AI analysis."
        )
        print("Alert email sent.")
    else:
        print("No price drops detected.")


if __name__ == "__main__":
    run_agent()
