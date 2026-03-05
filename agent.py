import pandas as pd
import sqlite3
import smtplib
import os
from email.mime.text import MIMEText
from datetime import datetime

<<<<<<< HEAD

# ==============================
# Email configuration
# ==============================

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")


def send_email(product, brand, old_price, new_price, drop):

    if not EMAIL_USER or not EMAIL_PASS:
        print("Email credentials missing. Skipping email.")
        return

    subject = "Price Drop Alert"

    body = f"""
Price drop detected!

Product: {brand} {product}

Old Price: Rs {old_price}
New Price: Rs {new_price}

Price Drop: Rs {drop}

Check your dashboard for more details.
"""

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_USER
    msg["To"] = EMAIL_USER

    try:
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

    except Exception as e:
        print("Email failed:", e)


# ==============================
# Create database table
# ==============================

=======
>>>>>>> a8d43d1 (added email alert functionality)
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


<<<<<<< HEAD
# ==============================
# Insert alert into database
# ==============================

=======
>>>>>>> a8d43d1 (added email alert functionality)
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


<<<<<<< HEAD
# ==============================
# AI decision logic
# ==============================

=======
>>>>>>> a8d43d1 (added email alert functionality)
def generate_decision(product, brand, drop, percent):

    if percent >= 10:
        decision = "BUY NOW: Price of " + brand + " " + product + " dropped by Rs " + str(drop)

    elif percent >= 5:
        decision = "Good deal: Price dropped by Rs " + str(drop)

    else:
        decision = "Minor price drop detected"

    return decision


<<<<<<< HEAD
# ==============================
# Run agent
# ==============================

=======
>>>>>>> a8d43d1 (added email alert functionality)
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

<<<<<<< HEAD
            send_email(product, brand, old_price, new_price, drop)

            print("Price drop detected for", product, "(" + brand + ")")


# ==============================
# Start agent
# ==============================

=======
            print("Price drop detected for", product, "(" + brand + ")")


>>>>>>> a8d43d1 (added email alert functionality)
if __name__ == "__main__":
    run_agent()
