import requests
from bs4 import BeautifulSoup


def get_price(url):

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code != 200:
            print("Failed to load page")
            return None

        soup = BeautifulSoup(response.content, "html.parser")

        price = None

        # Try multiple Amazon price selectors
        selectors = [
            "#priceblock_ourprice",
            "#priceblock_dealprice",
            "#priceblock_saleprice",
            ".a-price .a-offscreen",
            ".a-price-whole",
        ]

        for selector in selectors:
            tag = soup.select_one(selector)
            if tag:
                price_text = tag.get_text()
                price_text = (
                    price_text.replace("₹", "")
                    .replace(",", "")
                    .strip()
                )
                try:
                    price = float(price_text)
                    break
                except:
                    continue

        if price is None:
            print("Price not found on page")
            return None

        return price

    except Exception as e:
        print("Error scraping price:", e)
        return None
