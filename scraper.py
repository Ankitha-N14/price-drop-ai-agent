import requests
from bs4 import BeautifulSoup


def get_price(url):

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code != 200:
            print("Failed to load page")
            return None

        soup = BeautifulSoup(response.content, "lxml")

        # Possible Amazon price selectors
        selectors = [
            ".a-price .a-offscreen",
            "#priceblock_ourprice",
            "#priceblock_dealprice",
            "#priceblock_saleprice",
            ".a-price-whole"
        ]

        price = None

        for selector in selectors:
            tag = soup.select_one(selector)
            if tag:
                price = tag.text
                break

        if not price:
            print("Price not found on page")
            return None

        # Clean the price
        price = price.replace("₹", "").replace(",", "").strip()

        return float(price)

    except Exception as e:
        print("Error scraping price:", e)
        return None
