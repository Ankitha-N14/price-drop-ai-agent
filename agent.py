import pandas as pd
import sqlite3
import smtplib
import os
import requests
from bs4 import BeautifulSoup
from email.mime.text import MIMEText
from datetime import datetime


EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")


# -------------------------
# Scrape price from Amazon
# -------------------------

def get_price(url):

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    page = requests.get(url, headers=headers)

    soup = BeautifulSoup(page.content, "html.parser")

    price = soup.find("span", {"class": "a-price-whole"})

    if price:
        return int(price.text.replace(",", ""))

    return None


# -------------------------
# Email alerts
# -------------------------

def send_email(product, brand, old_price, new_price, drop):

    if not EMAIL_USER or not EMAIL_PASS:
        print("Email credentials missing")
        return

    subject = "Price Drop Alert"

    body = f"""
Price drop detected!

Product: {brand} {product}

Old Price: Rs {old_price}
New Price: Rs {new_price}

Drop: Rs {drop}
"""

    msg = MIMEText(body)

    msg["Subject"] = subject
    msg["From"] = EMAIL_USER
    msg["To"] = EMAIL_USER

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()

    server.login(EMAIL_USER, EMAIL_PASS)

    server.sendmail(
        EMAIL_USER,
        EMAIL_USER,
        msg.as_string()
    )

    server.quit()

    print("Email sent for", product)


# -------------------------
# Database
# -------------------------

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


# -------------------------
# Insert alert
# -------------------------

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


# -------------------------
# AI decision logic
# -------------------------

def generate_decision(product, brand, drop, percent):

    if percent >= 10:
        decision = "BUY NOW: Price of " + brand + " " + product + " dropped by Rs " + str(drop)

    elif percent >= 5:
        decision = "Good deal: Price dropped by Rs " + str(drop)

    else:
        decision = "Minor price drop detected"

    return decision


# -------------------------
# Run agent
# -------------------------

def run_agent():

    print("Checking prices...")

    create_table()

    df = pd.read_csv("products.csv")

    for index, row in df.iterrows():

        product = row["product"]
        brand = row["brand"]
        seller = row["seller"]
        url = row["url"]

        new_price = get_price(url)

        if new_price is None:
            continue

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT new_price FROM alerts WHERE product=? ORDER BY id DESC LIMIT 1",
            (product,)
        )

        result = cursor.fetchone()

        conn.close()

        if result:

            old_price = result[0]

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

                send_email(product, brand, old_price, new_price, drop)

                print("Price drop detected for", product)

        else:

            insert_alert(
                product,
                brand,
                seller,
                new_price,
                new_price,
                0,
                0,
                "Initial price recorded"
            )


if __name__ == "__main__":
    run_agent()
