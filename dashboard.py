"""
dashboard.py — Data-loading helpers for streamlit_app.py
All pandas / CSV work lives here.
"""

import csv
import json
import logging
import os
import shutil
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

log = logging.getLogger(__name__)

PRODUCTS_CSV = Path("products.csv")
HISTORY_CSV  = Path("price_history.csv")
CONFIG_FILE  = Path("config.json")
LOG_FILE     = Path("agent.log")

PRODUCTS_FIELDS = ["product_id", "name", "url", "threshold", "last_price", "last_checked"]
HISTORY_FIELDS  = [
    "product_id", "name", "url", "site",
    "price", "currency", "threshold",
    "alert_triggered", "timestamp",
]


# ── Products ──────────────────────────────────────────────────────────────────

def load_products() -> pd.DataFrame:
    if not PRODUCTS_CSV.exists():
        return pd.DataFrame(columns=PRODUCTS_FIELDS)
    df = pd.read_csv(PRODUCTS_CSV, dtype=str).fillna("")
    df.columns = df.columns.str.strip()
    if "price_threshold" in df.columns and "threshold" not in df.columns:
        df.rename(columns={"price_threshold": "threshold"}, inplace=True)
    for col in ("threshold", "last_price"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    if "last_checked" in df.columns:
        df["last_checked"] = pd.to_datetime(df["last_checked"], errors="coerce")
    return df


def _atomic_write(path: Path, fieldnames: list, rows: list[dict]):
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


def save_products(df: pd.DataFrame):
    df.to_csv(PRODUCTS_CSV, index=False)


def add_product(product_id: str, name: str, url: str, threshold: float):
    df = load_products()
    new = pd.DataFrame([{
        "product_id": product_id, "name": name, "url": url,
        "threshold": threshold, "last_price": None, "last_checked": None,
    }])
    df = pd.concat([df, new], ignore_index=True)
    save_products(df)


def delete_product(product_id: str):
    df = load_products()
    df = df[df["product_id"].astype(str) != str(product_id)]
    save_products(df)


# ── History ───────────────────────────────────────────────────────────────────

def load_history(days: int = 30) -> pd.DataFrame:
    if not HISTORY_CSV.exists():
        return pd.DataFrame(columns=HISTORY_FIELDS)
    df = pd.read_csv(HISTORY_CSV, dtype=str).fillna("")
    df.columns = df.columns.str.strip()
    df["price"]     = pd.to_numeric(df.get("price",     pd.Series(dtype=str)), errors="coerce")
    df["threshold"] = pd.to_numeric(df.get("threshold", pd.Series(dtype=str)), errors="coerce")
    df["timestamp"] = pd.to_datetime(df.get("timestamp", pd.Series(dtype=str)), errors="coerce")
    cutoff = datetime.now() - timedelta(days=days)
    return df[df["timestamp"] >= cutoff].sort_values("timestamp")


def price_trend(product_id: str, days: int = 30) -> pd.DataFrame:
    df = load_history(days)
    if df.empty or "product_id" not in df.columns:
        return pd.DataFrame()
    sub = df[df["product_id"].astype(str) == str(product_id)]
    return sub[["timestamp", "price", "threshold"]].dropna(subset=["price"])


def alerts_history(days: int = 30) -> pd.DataFrame:
    df = load_history(days)
    if df.empty or "alert_triggered" not in df.columns:
        return pd.DataFrame()
    return df[df["alert_triggered"].str.upper() == "YES"]


# ── Summary ───────────────────────────────────────────────────────────────────

def summary_stats() -> dict:
    products = load_products()
    history  = load_history(days=7)
    alerts   = alerts_history(days=7)
    below    = 0
    if not products.empty and "last_price" in products.columns and "threshold" in products.columns:
        m = (
            products["last_price"].notna()
            & products["threshold"].notna()
            & (products["threshold"] > 0)
            & (products["last_price"] <= products["threshold"])
        )
        below = int(m.sum())
    return {
        "total_products":  len(products),
        "checks_last_7d":  len(history),
        "alerts_last_7d":  len(alerts),
        "below_threshold": below,
    }


# ── Config ────────────────────────────────────────────────────────────────────

def load_config() -> dict:
    defaults = {
        "check_interval_seconds": 3600,
        "request_timeout": 20,
        "retry_attempts": 3,
        "EMAIL_SENDER":   "",
        "EMAIL_PASSWORD": "",
        "EMAIL_RECEIVER": "",
        "SMTP_HOST":      "smtp.gmail.com",
        "SMTP_PORT":      587,
    }
    if CONFIG_FILE.exists():
        try:
            return {**defaults, **json.loads(CONFIG_FILE.read_text())}
        except (json.JSONDecodeError, OSError):
            pass
    return defaults


def save_config(cfg: dict):
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2))
    log.info("config.json saved.")


# ── Log ───────────────────────────────────────────────────────────────────────

def read_log(lines: int = 200) -> str:
    if not LOG_FILE.exists():
        return "No log file yet. Run the agent first."
    with open(LOG_FILE, encoding="utf-8", errors="replace") as f:
        return "".join(f.readlines()[-lines:])


def export_history_csv() -> bytes:
    return load_history(days=365).to_csv(index=False).encode("utf-8")
