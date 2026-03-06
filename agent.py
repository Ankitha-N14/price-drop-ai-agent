import time
import schedule
import pandas as pd

from scraper import get_price
from ai_logic import price_decision
from notifier import send_email

FILE = "products.csv"


def check_prices():

    print("Checking prices...")

    try:
        df = pd.read_csv(FILE)
    except:
        print("No products found.")
        return

    for i, row in df.iterrows():

        url = row["url"]
        product = row["product"]
        email = row["email"]

        price = get_price(url)

        if price is None:
            print("Price not found for", product)
            continue

        last_price = row["current_price"]

        df.at[i, "last_price"] = last_price
        df.at[i, "current_price"] = price

        decision = price_decision(price, last_price)

        df.at[i, "ai_decision"] = decision

        print(product, ":", price)

        # send email if price dropped
        if last_price != 0 and price < last_price:

            print("Price dropped! Sending email...")

            send_email(
                email,
                product,
                price,
                url
            )

    df.to_csv(FILE, index=False)


print("Agent running...")

# run immediately when starting
check_prices()

# schedule continuous monitoring
schedule.every(5).minutes.do(check_prices)

while True:

    schedule.run_pending()

    time.sleep(5)
