import pandas as pd
from notifier import send_email

def run_agent():
    df = pd.read_csv("prices.csv")

    # Sort to ensure correct comparison
    df = df.reset_index()

    alerts = []

    # Group by product + brand + seller
    grouped = df.groupby(["product", "brand", "seller"])

    for (product, brand, seller), group in grouped:
        if len(group) < 2:
            continue

        previous_price = group.iloc[-2]["price"]
        current_price = group.iloc[-1]["price"]

        if current_price < previous_price:
            drop = previous_price - current_price
            percent = (drop / previous_price) * 100

            alerts.append(
                f"""
Product: {product}
Brand: {brand}
Seller: {seller}
Old Price: ₹{previous_price}
New Price: ₹{current_price}
Drop: ₹{drop} ({percent:.2f}%)
"""
            )

    if alerts:
        message = "MULTI-SELLER PRICE DROP ALERT 🚨\n\n"
        message += "\n--------------------------------\n".join(alerts)

        send_email("Price Drop Detected Across Sellers!", message)
        print("Alert email sent.")
    else:
        print("No price drops detected.")

if __name__ == "__main__":
    run_agent()
