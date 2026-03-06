import requests
import re

def get_price(url):

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }

    try:
        r = requests.get(url, headers=headers)
        html = r.text

        # Amazon embeds price in JSON sometimes
        price_match = re.search(r'"priceToPay"\s*:\s*\{"amount"\s*:\s*([\d\.]+)', html)

        if price_match:
            return float(price_match.group(1))

        # fallback selector
        price_match = re.search(r'₹\s?([\d,]+)', html)

        if price_match:
            price = price_match.group(1).replace(",", "")
            return float(price)

        print("Price not found on page")
        return None

    except Exception as e:
        print("Error:", e)
        return None
