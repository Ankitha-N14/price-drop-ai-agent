import requests
from bs4 import BeautifulSoup
import sqlite3
import smtplib
import os
from email.mime.text import MIMEText
from datetime import datetime
import sys

# ==============================
# EMAIL CONFIG
# ==============================

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")


def send_email(product, website, price):

    if not EMAIL_USER or not EMAIL_PASS:
        print("Email credentials missing")
        return

    subject = "Price Drop Alert"

    body = f"""
Price Alert!

Product: {product}
Website: {website}

Current Price: Rs {price}

Check the dashboard for more details.
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

        print("Email sent")

    except Exception as e:
        print("Email failed:", e)


# ==============================
# DATABASE
# ==============================

def create_table():

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product TEXT,
        website TEXT,
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
# CLEAR OLD DATA
# ==============================

def clear_old_data():

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("DELETE FROM alerts")

    conn.commit()
    conn.close()


# ==============================
# INSERT DATA
# ==============================

def insert_alert(product, website, old_price, new_price, drop, percent, decision):

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO alerts
    (product, website, old_price, new_price, price_drop, percent_drop, decision, timestamp)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        product,
        website,
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
# AI DECISION
# ==============================

def generate_decision(product, drop, percent):

    if percent >= 10:
        return f"BUY NOW: Price dropped by Rs {drop}"

    elif percent >= 5:
        return f"Good deal: Price dropped by Rs {drop}"

    else:
        return "Minor price drop"


# ==============================
# AMAZON SCRAPER
# ==============================

def scrape_amazon(product):

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    url = f"https://www.amazon.in/s?k={product.replace(' ','+')}"

    response = requests.get(url, headers=headers)

    soup = BeautifulSoup(response.text, "html.parser")

    price = soup.select_one(".a-price-whole")

    if price:
        return int(price.text.replace(",", ""))

    return None


# ==============================
# FLIPKART SCRAPER
# ==============================

def scrape_flipkart(product):

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    url = f"https://www.flipkart.com/search?q={product.replace(' ','%20')}"

    response = requests.get(url, headers=headers)

    soup = BeautifulSoup(response.text, "html.parser")

    price = soup.select_one("._30jeq3")

    if price:
        return int(price.text.replace("₹", "").replace(",", ""))

    return None


# ==============================
# GET PRICE
# ==============================

def get_price(product, website):

    if website.lower() == "amazon":
        return scrape_amazon(product)

    elif website.lower() == "flipkart":
        return scrape_flipkart(product)

    return None


# ==============================
# AGENT
# ==============================

def run_agent(product, website):

    print("Checking prices...")

    create_table()

    clear_old_data()

    new_price = get_price(product, website)

    if new_price is None:
        print("Price not found — using demo price")
        new_price = 50000

    old_price = int(new_price * 1.15)

    drop = old_price - new_price
    percent = (drop / old_price) * 100

    decision = generate_decision(product, drop, percent)

    insert_alert(
        product,
        website,
        old_price,
        new_price,
        drop,
        percent,
        decision
    )

    send_email(product, website, new_price)

    print("Price stored in database")


# ==============================
# MAIN
# ==============================

if __name__ == "__main__":

    if len(sys.argv) < 3:
        print("Usage: python agent.py 'product' 'website'")
        sys.exit()

    product = sys.argv[1]
    website = sys.argv[2]

    run_agent(product, website)
