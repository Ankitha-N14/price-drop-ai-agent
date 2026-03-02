import pandas as pd
from notifier import send_email

def run_agent():
    df = pd.read_csv("prices.csv")

    if len(df) < 2:
        print("Not enough data to compare prices.")
        return

    previous_price = df.iloc[-2]["price"]
    current_price = df.iloc[-1]["price"]
    product = df.iloc[-1]["product"]

    print(f"Previous price: {previous_price}")
    print(f"Current price: {current_price}")

    if current_price < previous_price:
        message = (
            f"Price Drop Alert!\n\n"
            f"Product: {product}\n"
            f"Old Price: ₹{previous_price}\n"
            f"New Price: ₹{current_price}"
        )
        send_email("Price Drop Detected!", message)
        print("Email sent.")
    else:
        print("No price drop detected.")

if __name__ == "__main__":
    run_agent()
