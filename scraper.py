"""
scraper.py
----------
Scrapes a target website and returns a list of structured items.

Default target: Hacker News front page (https://news.ycombinator.com).
To adapt this to another site (e.g. a product-price page), edit the
SITE_CONFIG dict below with the right URL and CSS selectors.
"""

import time
import json
import os
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# CONFIG - change this block to point the scraper at a different site
# ---------------------------------------------------------------------------
SITE_CONFIG = {
    "url": "https://news.ycombinator.com/",
    "item_selector": "tr.athing",          # one CSS selector per "item"
    "title_selector": "span.titleline > a",  # title/link within each item
    "extra_selector": None,                 # e.g. a price/score selector, optional
}

DATA_FILE = os.path.join(os.path.dirname(__file__), "scraped_data.json")
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; ScrapeBot/1.0)"}


def scrape_site(config: dict = SITE_CONFIG, limit: int = 20) -> list[dict]:
    """Fetch the page and extract a list of {title, url} items."""
    resp = requests.get(config["url"], headers=HEADERS, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    items = []
    for row in soup.select(config["item_selector"])[:limit]:
        title_el = row.select_one(config["title_selector"])
        if not title_el:
            continue
        entry = {
            "title": title_el.get_text(strip=True),
            "link": title_el.get("href", ""),
        }
        if config.get("extra_selector"):
            extra_el = row.select_one(config["extra_selector"])
            if extra_el:
                entry["extra"] = extra_el.get_text(strip=True)
        items.append(entry)
    return items


def save_snapshot(items: list[dict]) -> None:
    snapshot = {
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "source": SITE_CONFIG["url"],
        "items": items,
    }
    with open(DATA_FILE, "w") as f:
        json.dump(snapshot, f, indent=2)


def load_snapshot() -> dict | None:
    if not os.path.exists(DATA_FILE):
        return None
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def scrape_and_save() -> dict:
    items = scrape_site()
    save_snapshot(items)
    return load_snapshot()


def run_forever(interval_seconds: int = 300) -> None:
    """Standalone loop: scrape on a fixed interval. Useful if you want the
    scraper running as its own process instead of inside the Streamlit app."""
    while True:
        try:
            scrape_and_save()
            print(f"[{datetime.now()}] Scraped {SITE_CONFIG['url']}")
        except Exception as e:
            print(f"[{datetime.now()}] Scrape failed: {e}")
        time.sleep(interval_seconds)


if __name__ == "__main__":
    run_forever()
