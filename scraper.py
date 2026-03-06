import requests
from bs4 import BeautifulSoup

def get_price(url):

    headers = {
        "User-Agent":"Mozilla/5.0"
    }

    page = requests.get(url,headers=headers)
    soup = BeautifulSoup(page.content,"lxml")

    price = None

    selectors = [
        ".a-price-whole",
        ".price",
        "#priceblock_ourprice",
        "#priceblock_dealprice"
    ]

    for s in selectors:
        tag = soup.select_one(s)
        if tag:
            price = tag.text
            break

    if price:
        price = price.replace(",","").replace("₹","").strip()
        return float(price)

    return None
