import requests
from bs4 import BeautifulSoup
<<<<<<< HEAD
import time
import random
=======
>>>>>>> 236f75b (Improve scraper stability and add delay)


def get_price(url):

    headers = {
<<<<<<< HEAD
        "User-Agent": "Mozilla/5.0",
=======
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
>>>>>>> 236f75b (Improve scraper stability and add delay)
        "Accept-Language": "en-US,en;q=0.9"
    }

    try:
<<<<<<< HEAD
        time.sleep(random.randint(3,8))

        response = requests.get(url, headers=headers, timeout=10)

=======
        response = requests.get(url, headers=headers, timeout=10)

>>>>>>> 236f75b (Improve scraper stability and add delay)
        soup = BeautifulSoup(response.text, "html.parser")

        price_tag = soup.select_one("span.a-price span.a-offscreen")

        if price_tag:
<<<<<<< HEAD
            price = price_tag.text.replace("₹","").replace(",","").strip()
=======
            price = price_tag.text.replace("₹", "").replace(",", "").strip()
>>>>>>> 236f75b (Improve scraper stability and add delay)
            return float(price)

        if "Currently unavailable" in response.text:
            print("Product currently unavailable")
            return None

        print("Price not found on page")
        return None

    except Exception as e:
        print("Error:", e)
        return None
