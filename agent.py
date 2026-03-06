import time
import schedule
from database import load_products,save_products
from scraper import get_price
from ai_logic import price_decision
from notifier import send_email


def check_prices():

    df = load_products()

    for i,row in df.iterrows():

        price = get_price(row["url"])

        if price is None:
            continue

        last = row["current_price"]

        df.at[i,"last_price"] = last
        df.at[i,"current_price"] = price

        decision = price_decision(price,last)

        df.at[i,"ai_decision"] = decision

        if last != 0 and price < last:

            send_email(
                row["email"],
                row["product"],
                price,
                row["url"]
            )

    save_products(df)


schedule.every(5).minutes.do(check_prices)

print("Agent running...")

while True:

    schedule.run_pending()

    time.sleep(5)
