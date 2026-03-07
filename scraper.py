import requests
import re


def get_price(url):

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "en-US,en;q=0.9"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        html = response.text

        # Amazon price JSON
        match = re.search(r'"priceToPay"\s*:\s*\{"amount"\s*:\s*([\d\.]+)', html)

        if match:
            return float(match.group(1))

        # fallback price detection
        match = re.search(r'₹\s?([\d,]+)', html)

        if match:
            return float(match.group(1).replace(",", ""))

        print("Price not found on page")
        return None

    except Exception as e:
        print("Error:", e)
        return None
