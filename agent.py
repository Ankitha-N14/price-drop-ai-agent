"""
agent.py — Autonomous Price Monitor for Amazon India & Flipkart
Fixes applied:
  1. Verified CSS selectors for Amazon.in & Flipkart (2025)
  2. Anti-bot session with cookie warm-up + rotating User-Agent
  3. JSON-LD price fallback (works even when DOM selectors change)
  4. Atomic CSV writes — crash-safe, no data corruption
  5. Email-only alerts via notifier.py
"""

import csv
import json
import logging
import os
import random
import re
import shutil
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests
from bs4 import BeautifulSoup

from notifier import EmailNotifier

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("agent.log", encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)

PRODUCTS_CSV    = Path("products.csv")
HISTORY_CSV     = Path("price_history.csv")
CONFIG_FILE     = Path("config.json")
PRODUCTS_FIELDS = ["product_id", "name", "url", "threshold", "last_price", "last_checked"]
HISTORY_FIELDS  = ["product_id","name","url","site","price","currency","threshold","alert_triggered","timestamp"]
DEFAULT_CONFIG  = {"check_interval_seconds":3600,"request_timeout":20,"retry_attempts":3,"retry_delay":8}

# ── 2025-verified selectors ───────────────────────────────────────────────────
SELECTORS = {
    "amazon": {
        "price": [
            "span.a-price.aok-align-center span.a-offscreen",
            ".a-price .a-offscreen",
            "#corePrice_feature_div .a-offscreen",
            "#price_inside_buybox",
            "#priceblock_ourprice",
            "#priceblock_dealprice",
            "#priceblock_saleprice",
            "#actualPriceValue",
        ],
        "name":     ["#productTitle","h1.a-size-large"],
        "base_url": "https://www.amazon.in",
        "currency": "INR",
    },
    "flipkart": {
        "price": [
            "div.Nx9bqj.CxhGGd",
            "div._30jeq3._16Jk6d",
            "div._30jeq3",
            "._1vC4OE._3qQ9m1",
            "div.CEmiEU > div.Nx9bqj",
            "[class*='finalPrice']",
            "[class*='selling-price']",
        ],
        "name":     ["span.VU-ZEz","span.B_NuCI","h1.yhB1nd","h1._9E25nV"],
        "base_url": "https://www.flipkart.com",
        "currency": "INR",
    },
}

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
]


def load_config():
    cfg = DEFAULT_CONFIG.copy()
    if CONFIG_FILE.exists():
        try:
            cfg.update(json.loads(CONFIG_FILE.read_text()))
        except Exception as e:
            log.warning("Config error: %s", e)
    return cfg


def detect_site(url):
    u = url.lower()
    if "amazon" in u:   return "amazon"
    if "flipkart" in u: return "flipkart"
    raise ValueError(f"Unsupported site (only Amazon.in & Flipkart): {url}")


def parse_price(text):
    if not text: return None
    cleaned = re.sub(r"[^\d.]", "", text.strip()).rstrip(".")
    if not cleaned: return None
    try:   return round(float(cleaned), 2)
    except ValueError: return None


def build_session(site):
    s = requests.Session()
    s.headers.update({
        "User-Agent":               random.choice(USER_AGENTS),
        "Accept-Language":          "en-IN,en;q=0.9",
        "Accept":                   "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Encoding":          "gzip, deflate, br",
        "Referer":                  SELECTORS[site]["base_url"],
        "DNT":                      "1",
        "Connection":               "keep-alive",
        "Upgrade-Insecure-Requests":"1",
    })
    try:
        s.get(SELECTORS[site]["base_url"], timeout=10)
        time.sleep(random.uniform(1.0, 2.5))
    except Exception:
        pass
    return s


def scrape(url, config):
    site   = detect_site(url)
    sel    = SELECTORS[site]
    result = {"name":url,"price":None,"currency":sel["currency"],
               "url":url,"site":site,
               "timestamp":datetime.now().isoformat(timespec="seconds"),"error":None}

    session  = build_session(site)
    attempts = config["retry_attempts"]
    delay    = config["retry_delay"]

    for attempt in range(1, attempts + 1):
        try:
            session.headers["User-Agent"] = random.choice(USER_AGENTS)
            resp = session.get(url, timeout=config["request_timeout"], allow_redirects=True)
            resp.raise_for_status()

            snippet = resp.text[:3000].lower()
            if any(kw in snippet for kw in ["captcha","robot check","enter the characters","unusual traffic"]):
                log.warning("[%s] Bot-wall attempt %d", site, attempt)
                time.sleep(delay * attempt * 3)
                continue

            soup  = BeautifulSoup(resp.content, "lxml")
            price = None

            # CSS selectors
            for css in sel["price"]:
                tag = soup.select_one(css)
                if tag:
                    raw   = tag.get("content") or tag.get_text(strip=True)
                    price = parse_price(raw)
                    if price and price > 1:
                        break

            # JSON-LD fallback
            if not price:
                for script in soup.find_all("script", type="application/ld+json"):
                    try:
                        data   = json.loads(script.string or "{}")
                        offers = data.get("offers", {})
                        if isinstance(offers, list): offers = offers[0]
                        raw_p  = str(offers.get("price") or data.get("price") or "")
                        price  = parse_price(raw_p)
                        if price and price > 1: break
                    except Exception:
                        continue

            name = url
            for css in sel["name"]:
                tag = soup.select_one(css)
                if tag:
                    name = tag.get_text(strip=True)[:250]
                    break

            result.update({"name":name,"price":price,
                            "timestamp":datetime.now().isoformat(timespec="seconds")})
            status = f"Rs.{price:,.2f}" if price else "PRICE NOT FOUND"
            log.info("[%s] %s -> %s", site.upper(), name[:55], status)
            return result

        except requests.HTTPError as e:
            result["error"] = f"HTTP {e.response.status_code}"
            log.warning("HTTP %s attempt %d", e.response.status_code, attempt)
        except requests.RequestException as e:
            result["error"] = str(e)
            log.warning("Network error attempt %d: %s", attempt, e)

        if attempt < attempts:
            time.sleep(delay * attempt + random.uniform(1, 4))

    log.error("All %d attempts failed for %s", attempts, url)
    return result


def _atomic_write(path, fieldnames, rows):
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            w.writeheader()
            w.writerows(rows)
        shutil.move(tmp, path)
    except Exception:
        try: os.unlink(tmp)
        except OSError: pass
        raise


def ensure_products_csv():
    if PRODUCTS_CSV.exists(): return
    sample = [
        {"product_id":"P001","name":"Sample Amazon Product",
         "url":"https://www.amazon.in/dp/B08N5LNQCX","threshold":"999","last_price":"","last_checked":""},
        {"product_id":"P002","name":"Sample Flipkart Product",
         "url":"https://www.flipkart.com/sample/p/itm000","threshold":"499","last_price":"","last_checked":""},
    ]
    _atomic_write(PRODUCTS_CSV, PRODUCTS_FIELDS, sample)
    log.info("Created sample products.csv — replace with your real URLs.")


def load_products():
    ensure_products_csv()
    rows = []
    with open(PRODUCTS_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            row = {k.strip(): v.strip() for k, v in row.items()}
            thresh = row.get("threshold") or row.get("price_threshold") or "0"
            try:   row["threshold"] = float(thresh)
            except ValueError: row["threshold"] = 0.0
            rows.append(row)
    return rows


def update_product(product_id, price, ts):
    rows = []
    fieldnames = PRODUCTS_FIELDS[:]
    with open(PRODUCTS_CSV, newline="", encoding="utf-8") as f:
        reader     = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or fieldnames)
        for row in reader:
            if row.get("product_id","").strip() == product_id:
                row["last_price"]   = str(price) if price is not None else ""
                row["last_checked"] = ts
            rows.append(row)
    for col in ("last_price","last_checked"):
        if col not in fieldnames: fieldnames.append(col)
    _atomic_write(PRODUCTS_CSV, fieldnames, rows)


def append_history(product, scraped):
    price     = scraped.get("price")
    threshold = float(product.get("threshold", 0))
    alerted   = "YES" if (price is not None and threshold > 0 and price <= threshold) else "NO"
    row = {
        "product_id": product.get("product_id",""),
        "name":       scraped.get("name", product.get("name","")),
        "url":        product.get("url",""),
        "site":       scraped.get("site",""),
        "price":      price if price is not None else "N/A",
        "currency":   scraped.get("currency","INR"),
        "threshold":  threshold,
        "alert_triggered": alerted,
        "timestamp":  scraped.get("timestamp",""),
    }
    needs_header = not HISTORY_CSV.exists() or HISTORY_CSV.stat().st_size == 0
    with open(HISTORY_CSV, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=HISTORY_FIELDS, extrasaction="ignore")
        if needs_header: w.writeheader()
        w.writerow(row)


def run_once(config, notifier):
    products = load_products()
    log.info("-- Price check: %d product(s) --", len(products))
    triggered = []
    for product in products:
        url = product.get("url","").strip()
        if not url or url.startswith("#"): continue
        try:
            detect_site(url)
        except ValueError as e:
            log.warning("Skipping: %s", e)
            continue

        scraped   = scrape(url, config)
        price     = scraped.get("price")
        threshold = float(product.get("threshold", 0))

        append_history(product, scraped)
        update_product(product.get("product_id",""), price, scraped["timestamp"])

        if price is not None and threshold > 0 and price <= threshold:
            name = scraped.get("name", url)[:80]
            msg  = (
                f"Product : {name}\n"
                f"Price   : Rs.{price:,.2f}\n"
                f"Target  : Rs.{threshold:,.2f}\n"
                f"Saving  : Rs.{threshold - price:,.2f}\n"
                f"URL     : {url}\n"
                f"Time    : {scraped['timestamp']}"
            )
            log.info("ALERT -- %s @ Rs.%s (threshold Rs.%s)", name[:40], price, threshold)
            notifier.send(msg, subject=f"Price Drop: {name[:50]}")
            triggered.append(scraped)

        time.sleep(random.uniform(3, 7))

    log.info("-- Done. %d alert(s) sent --", len(triggered))
    return triggered


def run_loop():
    config   = load_config()
    notifier = EmailNotifier()
    interval = config["check_interval_seconds"]
    log.info("Agent started. Interval: %ds", interval)
    while True:
        try:
            run_once(config, notifier)
        except KeyboardInterrupt:
            log.info("Stopped.")
            break
        except Exception as e:
            log.exception("Unexpected error: %s", e)
        log.info("Next check in %ds...", interval)
        time.sleep(interval)


if __name__ == "__main__":
    run_loop()
