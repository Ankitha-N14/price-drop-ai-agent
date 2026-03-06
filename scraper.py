from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time


def get_price(url):

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-blink-features=AutomationControlled")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    driver.get(url)

    time.sleep(3)

    price = None

    selectors = [
        "span.a-price.aok-align-center span.a-offscreen",
        "#priceblock_ourprice",
        "#priceblock_dealprice",
        ".a-price .a-offscreen"
    ]

    for selector in selectors:
        try:
            element = driver.find_element(By.CSS_SELECTOR, selector)
            price_text = element.text.replace("₹", "").replace(",", "")
            price = float(price_text)
            break
        except:
            continue

    driver.quit()

    if price:
        return price
    else:
        print("Price not found on page")
        return None
