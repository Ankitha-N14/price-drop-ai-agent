"""
Autonomous E-Commerce Price Monitoring Agent
Scrapes product prices and triggers alerts when thresholds are crossed.
"""

import csv
import json
import logging
import os
import random
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests
from bs4 import BeautifulSoup

from notifier import Notifier

# ── Logging setup ────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("agent.log", encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────────
PRODUCTS_CSV = Path("products.csv")
HISTORY_CSV  = Path("price_history.csv")
CONFIG_FILE  = Path("config.json")

DEFAULT_CONFIG = {
    "check_interval_seconds": 3600,
    "request_timeout": 15,
    "retry_attempts": 3,
    "retry_delay": 5,
    "user_agents": [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
        "(KHTML, like Gecko) Version/17.3 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0",
    ],
}

SITE_SELECTORS = {
    "amazon": {
        "price": [
            "#priceblock_ourprice",
            "#priceblock_dealprice",
            ".a-price .a-offscreen",
            "span.a-price-whole",
            "#price_inside_buybox",
        ],
        "name": ["#productTitle", "h1.a-size-large"],
    },
    "flipkart": {
        "price": ["._30jeq3._16Jk6d", "._30jeq3", "div._25b18c ._30jeq3"],
        "name":  ["span.B_NuCI", "h1.yhB1nd"],
    },
    "ebay": {
        "price": ["#prcIsum", ".x-price-primary span", "#mm-saleDscPrc"],
        "name":  ["h1.it-ttl", "#itemTitle"],
    },
    "generic": {
        "price": [
            "[class*='price']",
            "[id*='price']",
            "[class*='Price']",
            "span[itemprop='price']",
            "meta[itemprop='price']",
        ],
        "name": ["h1", "[class*='product-title']", "[class*='productTitle']"],
    },
}


def load_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE) as f:
                cfg = json.load(f)
            return {**DEFAULT_CONFIG, **cfg}
        except (json.JSONDecodeError, OSError) as e:
            log.warning("Config load failed (%s); using defaults.", e)
    return DEFAULT_CONFIG.copy()


def detect_site(url: str) -> str:
    url_lower = url.lower()
    for site in ("amazon", "flipkart", "ebay"):
        if site in url_lower:
            return site
    return "generic"


def parse_price(raw: str) -> Optional[float]:
    """Extract a float from a messy price string."""
    if not raw:
        return None
    cleaned = re.sub(r"[^\d.,]", "", raw.strip())
    # Handle Indian lakh format: 1,00,000
    cleaned = cleaned.replace(",", "")
    try:
        return float(cleaned)
    except ValueError:
        return None


def scrape_product(url: str, config: dict) -> dict:
    """
    Fetch a product page and return {name, price, currency, url, timestamp}.
    Returns price=None on failure.
    """
    site      = detect_site(url)
    selectors = SITE_SELECTORS[site]
    headers   = {
        "User-Agent": random.choice(config["user_agents"]),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Referer": "https://www.google.com/",
    }

    for attempt in range(1, config["retry_attempts"] + 1):
        try:
            resp = requests.get(
                url,
                headers=headers,
                timeout=config["request_timeout"],
                allow_redirects=True,
            )
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            # ── Extract price ───────────────────────────────────────────
            price = None
            for sel in selectors["price"]:
                tag = soup.select_one(sel)
                if tag:
                    raw = tag.get("content") or tag.get_text()
                    price = parse_price(raw)
                    if price:
                        break

            # ── Extract name ────────────────────────────────────────────
            name = url  # fallback
            for sel in selectors["name"]:
                tag = soup.select_one(sel)
                if tag:
                    name = tag.get_text(strip=True)[:200]
                    break

            # ── Detect currency ─────────────────────────────────────────
            currency = "INR" if "flipkart" in url or ".in" in url else "USD"

            result = {
                "name":      name,
                "price":     price,
                "currency":  currency,
                "url":       url,
                "site":      site,
                "timestamp": datetime.now().isoformat(timespec="seconds"),
            }
            log.info("Scraped [%s] %s → %s %s", site, name[:60], price, currency)
            return result

        except requests.RequestException as e:
            log.warning("Attempt %d/%d failed for %s: %s", attempt, config["retry_attempts"], url, e)
            if attempt < config["retry_attempts"]:
                time.sleep(config["retry_delay"] * attempt)

    log.error("All attempts failed for %s", url)
    return {
        "name": url, "price": None, "currency": "N/A",
        "url": url, "site": site,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    }


def load_products() -> list[dict]:
    """Read products.csv → list of dicts."""
    if not PRODUCTS_CSV.exists():
        log.warning("products.csv not found — creating sample.")
        _create_sample_products()

    products = []
    with open(PRODUCTS_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row = {k.strip(): v.strip() for k, v in row.items()}
            # Normalise threshold field name
            row.setdefault("threshold", row.get("price_threshold", "0"))
            try:
                row["threshold"] = float(row["threshold"])
            except ValueError:
                row["threshold"] = 0.0
            products.append(row)
    return products


def _create_sample_products():
    """Write a starter products.csv so the agent can run immediately."""
    sample = [
        {
            "product_id": "P001",
            "name": "Sample Product 1",
            "url": "https://www.amazon.in/dp/B08N5LNQCX",
            "threshold": "999.00",
            "last_price": "",
            "last_checked": "",
        },
        {
            "product_id": "P002",
            "name": "Sample Product 2",
            "url": "https://www.flipkart.com/some-product/p/itm123",
            "threshold": "499.00",
            "last_price": "",
            "last_checked": "",
        },
    ]
    with open(PRODUCTS_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(sample[0].keys()))
        writer.writeheader()
        writer.writerows(sample)
    log.info("Created sample products.csv")


def update_product_row(product: dict, scraped: dict):
    """Persist last_price and last_checked back into products.csv."""
    rows = []
    with open(PRODUCTS_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        for row in reader:
            if row.get("product_id") == product.get("product_id") or row.get("url") == product.get("url"):
                row["last_price"]   = str(scraped.get("price", ""))
                row["last_checked"] = scraped.get("timestamp", "")
            rows.append(row)

    with open(PRODUCTS_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def append_history(product: dict, scraped: dict):
    """Append one row to price_history.csv."""
    file_exists = HISTORY_CSV.exists()
    fieldnames = [
        "product_id", "name", "url", "price", "currency",
        "threshold", "alert_triggered", "timestamp",
    ]
    price     = scraped.get("price")
    threshold = float(product.get("threshold", 0))
    alerted   = "YES" if (price is not None and threshold > 0 and price <= threshold) else "NO"

    with open(HISTORY_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            "product_id":       product.get("product_id", ""),
            "name":             scraped.get("name", product.get("name", "")),
            "url":              product.get("url", ""),
            "price":            price if price is not None else "N/A",
            "currency":         scraped.get("currency", ""),
            "threshold":        threshold,
            "alert_triggered":  alerted,
            "timestamp":        scraped.get("timestamp", ""),
        })


def run_once(config: dict, notifier: Notifier):
    """Single monitoring pass over all products."""
    products = load_products()
    log.info("Starting check for %d products.", len(products))
    alerts = []

    for product in products:
        url = product.get("url", "").strip()
        if not url or url.startswith("#"):
            continue

        scraped   = scrape_product(url, config)
        price     = scraped.get("price")
        threshold = float(product.get("threshold", 0))

        append_history(product, scraped)
        update_product_row(product, scraped)

        # ── Alert logic ─────────────────────────────────────────────────
        if price is not None and threshold > 0 and price <= threshold:
            msg = (
                f"🎉 Price Alert!\n"
                f"Product : {scraped['name'][:80]}\n"
                f"Price   : {scraped['currency']} {price:,.2f}\n"
                f"Target  : {scraped['currency']} {threshold:,.2f}\n"
                f"URL     : {url}\n"
                f"Time    : {scraped['timestamp']}"
            )
            log.info("ALERT triggered: %s", msg.splitlines()[1])
            notifier.send(msg)
            alerts.append(scraped)

        # polite delay between requests
        time.sleep(random.uniform(2, 5))

    log.info("Check complete. Alerts sent: %d", len(alerts))
    return alerts


def run_loop():
    """Continuous monitoring loop."""
    config   = load_config()
    notifier = Notifier()
    log.info("Agent started. Interval: %ds", config["check_interval_seconds"])

    while True:
        try:
            run_once(config, notifier)
        except Exception as e:
            log.exception("Unexpected error in run_once: %s", e)

        next_run = datetime.now().strftime("%H:%M:%S")
        log.info("Next check in %ds  (started at %s)", config["check_interval_seconds"], next_run)
        time.sleep(config["check_interval_seconds"])


if __name__ == "__main__":
    run_loop()
