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
        model="llama3-8b-8192",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content


def save_to_db(product, brand, seller, old_price, new_price, drop, percent, decision):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        "CREATE TABLE IF NOT EXISTS alerts ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "product TEXT, "
        "brand TEXT, "
        "seller TEXT, "
        "old_price REAL, "
        "new_price REAL, "
        "drop REAL, "
        "percent REAL, "
        "ai_decision TEXT, "
        "timestamp TEXT)"
    )

    cursor.execute(
        "SELECT COUNT(*) FROM alerts WHERE "
        "product=? AND brand=? AND seller=? AND old_price=? AND new_price=?",
        (product, brand, seller, old_price, new_price)
    )

    exists = cursor.fetchone()[0]

    if exists == 0:
        cursor.execute(
            "INSERT INTO alerts "
            "(product, brand, seller, old_price, new_price, drop, percent, ai_decision, timestamp) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                product,
                brand,
                seller,
                old_price,
                new_price,
                drop,
                percent,
                decision,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
        )
        conn.commit()
        conn.close()
        return True

    conn.close()
    return False


def run_agent():
    df = pd.read_csv("prices.csv")
    alerts = []

    grouped = df.groupby(["product", "brand", "seller"])

    for (product, brand, seller), group in grouped:

        if len(group) < 2:
            continue

        previous_price = group.iloc[-2]["price"]
        current_price = group.iloc[-1]["price"]

        if current_price < previous_price:

            drop = previous_price - current_price
            percent = (drop / previous_price) * 100

            decision = ai_analysis(
                product, brand, seller, previous_price, current_price
            )

            saved = save_to_db(
                product,
                brand,
                seller,
                previous_price,
                current_price,
                drop,
                percent,
                decision
            )

            if saved:
                message_block = (
                    "\nProduct: " + product +
                    "\nBrand: " + brand +
                    "\nSeller: " + seller +
                    "\nOld Price: Rs " + str(previous_price) +
                    "\nNew Price: Rs " + str(current_price) +
                    "\nDrop: Rs " + str(drop) +
                    " (" + str(round(percent, 2)) + "%)\n\n"
                    "AI Decision:\n" + decision + "\n"
                )
                alerts.append(message_block)

    if alerts:
        message = "AI MULTI SELLER PRICE DROP ALERT\n"
        message += "\n-----------------------------------\n".join(alerts)
        send_email("AI Price Drop Alert", message)
        print("Alert email sent.")
    else:
        print("No new price drops detected.")


if __name__ == "__main__":
    run_agent()
