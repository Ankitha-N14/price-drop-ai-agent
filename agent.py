import pandas as pd
import sqlite3
from datetime import datetime
from notifier import send_email
from langchain.chat_models import ChatGroq
from langchain.schema import HumanMessage
import os

def ai_analysis(product, brand, seller, old_price, new_price):
    llm = ChatGroq(
        groq_api_key=os.getenv("GROQ_API_KEY"),
        model_name="llama3-8b-8192"
    )

    prompt = f"""
    Product: {product}
    Brand: {brand}
    Seller: {seller}
    Old Price: ₹{old_price}
    New Price: ₹{new_price}

    Should the user BUY now or WAIT?
    Give short reasoning.
    """

    response = llm([HumanMessage(content=prompt)])
    return response.content


def save_to_db(product, brand, seller, old_price, new_price, drop, percent, ai_decision):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product TEXT,
            brand TEXT,
            seller TEXT,
            old_price REAL,
            new_price REAL,
            drop REAL,
            percent REAL,
            ai_decision TEXT,
            timestamp TEXT
        )
    """)

    cursor.execute("""
        INSERT INTO alerts 
        (product, brand, seller, old_price, new_price, drop, percent, ai_decision, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        product,
        brand,
        seller,
        old_price,
        new_price,
        drop,
        percent,
        ai_decision,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()
    conn.close()


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

            decision = ai_analysis(product, brand, seller, previous_price, current_price)

            save_to_db(product, brand, seller, previous_price, current_price, drop, percent, decision)

            alerts.append(f"""
Product: {product}
Brand: {brand}
Seller: {seller}
Old Price: ₹{previous_price}
New Price: ₹{current_price}
Drop: ₹{drop} ({percent:.2f}%)

AI Decision:
{decision}
""")

    if alerts:
        message = "MULTI-SELLER PRICE DROP ALERT 🚨\n\n"
        message += "\n-----------------------------------\n".join(alerts)
        send_email("AI Price Drop Alert", message)
        print("Alert email sent.")
    else:
        print("No price drops detected.")


if __name__ == "__main__":
    run_agent()
