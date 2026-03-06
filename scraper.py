import requests
from bs4 import BeautifulSoup


def get_price(url):

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)

        soup = BeautifulSoup(response.text, "html.parser")

        # main Amazon price selector
        price = soup.select_one("span.a-price span.a-offscreen")

        if price:
            price_text = price.text.replace("₹", "").replace(",", "").strip()
            return float(price_text)

        # if product unavailable
        if "Currently unavailable" in response.text:
            print("Product currently unavailable")
            return None

        print("Price not found on page")
        return None

    except Exception as e:
        print("Error:", e)
        return None
