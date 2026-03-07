import requests
from bs4 import BeautifulSoup
import time
import random


def get_price(url):

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122 Safari/537.36",
        "Accept-Language": "en-IN,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive"
    }

    try:
        time.sleep(random.randint(2,5))

        response = requests.get(url, headers=headers, timeout=15)

        soup = BeautifulSoup(response.text, "html.parser")

        price_tag = soup.select_one("span.a-price span.a-offscreen")

        if price_tag:
            price = price_tag.text.replace("₹","").replace(",","").strip()
            return float(price)

        print("Price not found on page")
        return None

    except Exception as e:
        print("Error:", e)
        return None
