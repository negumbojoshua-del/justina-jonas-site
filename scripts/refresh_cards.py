```python
"""
Scheduled Facebook post refresher.

Runs from GitHub Actions every 4 hours.
Opens Hon. Jonas's personal Facebook profile in headless Chromium,
tries to extract the most recent posts, and re-splices them into the
Home > Recent Highlights cards and Parliamentary > Recent Sessions
strip in index.html.

Design principles:
- Fail SILENTLY when Facebook gates the scrape. Never break the site.
- Only touch the AUTO-* marker regions in index.html. Never edit static
  areas like the hero, contact, or biography.
- Store the last-scraped-hash in data/latest_posts.json so we only commit
  when content actually changed.
"""
from __future__ import annotations
import hashlib
import io
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# --- Config -----------------------------------------------------------------

FB_URL = "https://www.facebook.com/justina.jonas.526"
PAGE_URL_FOR_LINKS = "https://www.facebook.com/hon.justina"
INDEX_HTML = Path("index.html")
STATE_JSON = Path("data/latest_posts.json")
MIN_POST_LEN = 90
MAX_CARDS = 4

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/121.0.0.0 Safari/537.36"
)

# --- Scrape -----------------------------------------------------------------


def scrape_posts() -> list[dict]:
    """Return a list of post dicts. Empty list if Facebook gates us."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("playwright not installed", file=sys.stderr)
        return []

    posts: list[dict] = []
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
            ],
        )
        context = browser.new_context(
            user_agent=USER_AGENT,
            locale="en-US",
            viewport={"width": 1280, "height": 900},
        )
        page = context.new_page()

        try:
            page.goto(FB_URL, wait_until="domcontentloaded", timeout=25_000)
        except Exception as e:
            print(f"navigation failed: {e}", file=sys.stderr)
            browser.close()
            return []

        # Let posts hydrate
        page.wait_for_timeout(6_000)

        # Best-effort dialog cleanup and "See more" expansion
        try:
            page.evaluate(
                """() => {
                    document.querySelectorAll('[role="dialog"]').forEach(d => d.remove());
                    Array.from(document.querySelectorAll('div[role="button"], span'))
                      .filter(e => (e.innerText || '').trim() === 'See more')
                      .forEach(b => { try { b.click(); } catch (e) {} });
                }"""
            )
        except Exception:
            pass

        page.wait_for_timeout(1_500)

        # Grab body innerText; parse long lines as post candidates
        try:
            body_text =
