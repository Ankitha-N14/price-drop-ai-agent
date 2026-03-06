import sqlite3
import smtplib
import os
import sys
import requests
from bs4 import BeautifulSoup
from email.mime.text import MIMEText
from datetime import datetime


# ==============================
# Email configuration
# ==============================

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")


def send_email(product, site, old_price, new_price, drop):

    if not EMAIL_USER or not EMAIL_PASS:
        print("Email credentials missing. Skipping email.")
        return

    subject = "Price Drop Alert"

    body = f"""
Price Drop Detected!

Product: {product}
Website: {site}

Old Price: Rs {old_price}
New Price: Rs {new_price}

Drop: Rs {drop}

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

        print("Email sent successfully")

    except Exception as e:
        print("Email failed:", e)


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
        return f"BUY NOW: Price of {brand} {product} dropped by Rs {drop}"

    elif percent >= 5:
        return f"Good deal: Price dropped by Rs {drop}"

    else:
        return "Minor price drop detected"


# ==============================
# Web Scraping
# ==============================

def get_price(product, site):

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:

        if site.lower() == "amazon":

            url = f"https://www.amazon.in/s?k={product}"

            r = requests.get(url, headers=headers)

            soup = BeautifulSoup(r.text, "html.parser")

            price = soup.select_one("span.a-price-whole")

            if price:
                return int(price.text.replace(",", ""))

            # fallback selector
            alt_price = soup.select_one(".a-price .a-offscreen")

            if alt_price:
                return int(
                    alt_price.text
                    .replace("₹", "")
                    .replace(",", "")
                    .strip()
                )


        if site.lower() == "flipkart":

            url = f"https://www.flipkart.com/search?q={product}"

            r = requests.get(url, headers=headers)

            soup = BeautifulSoup(r.text, "html.parser")

            price = soup.select_one("._30jeq3")

            if price:
                return int(
                    price.text
                    .replace("₹", "")
                    .replace(",", "")
                    .strip()
                )

    except Exception as e:

        print("Scraping error:", e)

    return None


# ==============================
# Run Agent
# ==============================

def run_agent(product, site):

    print("Checking prices...")

    create_table()

    new_price = get_price(product, site)

    if new_price is None:

        print("Price not found for this product.")
        return

    # Simulated previous price
    old_price = new_price + 1000

    drop = old_price - new_price

    percent = (drop / old_price) * 100

    decision = generate_decision(product, site, drop, percent)

    insert_alert(
        product,
        site,
        site,
        old_price,
        new_price,
        drop,
        percent,
        decision
    )

    send_email(product, site, old_price, new_price, drop)

    print("Price stored in database.")


# ==============================
# Start Agent
# ==============================

if __name__ == "__main__":

    if len(sys.argv) < 3:

        print("Usage: python agent.py <product> <site>")
        print("Example: python agent.py 'sony earbuds' amazon")

    else:

        product = sys.argv[1]
        site = sys.argv[2]

        run_agent(product, site)
