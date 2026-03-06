import requests
from bs4 import BeautifulSoup

def get_price(url):

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }

    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, "html.parser")

        price_tag = soup.select_one(".a-price .a-offscreen")

        if price_tag:
            price = price_tag.text.replace("₹","").replace(",","").strip()
            return float(price)

        print("Price not found on page")
        return None

    except Exception as e:
        print("Error:", e)
        return None
