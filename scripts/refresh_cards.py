"""
Scheduled Facebook post refresher.
Runs from GitHub Actions every 4 hours.
Opens Hon. Jonas's Facebook profile in headless Chromium, tries to extract
recent posts, and re-splices them into index.html marker regions.
Fails silently when Facebook gates the scrape.
"""
from __future__ import annotations
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

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


def scrape_posts():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("playwright not installed", file=sys.stderr)
        return []

    posts = []
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
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
        page.wait_for_timeout(6_000)
        try:
            page.evaluate(
                "() => { document.querySelectorAll('[role=\"dialog\"]').forEach(d => d.remove()); "
                "Array.from(document.querySelectorAll('div[role=\"button\"], span'))"
                ".filter(e => (e.innerText || '').trim() === 'See more')"
                ".forEach(b => { try { b.click(); } catch (e) {} }); }"
            )
        except Exception:
            pass
        page.wait_for_timeout(1_500)
        try:
            body_text = page.evaluate("() => document.body.innerText || ''")
        except Exception as e:
            print(f"innerText failed: {e}", file=sys.stderr)
            browser.close()
            return []
        browser.close()

    lines = [ln.strip() for ln in body_text.split("\n")]
    candidates = []
    for ln in lines:
        if len(ln) < MIN_POST_LEN:
            continue
        low = ln.lower()
        if low in {"facebook", "justina jonas"}:
            continue
        if low.startswith(("all reactions", "comment as", "see more", "see less")):
            continue
        if sum(c.isalpha() for c in ln) < 40:
            continue
        candidates.append(ln)
    seen = set()
    unique = []
    for c in candidates:
        key = c[:100]
        if key in seen:
            continue
        seen.add(key)
        unique.append(c)
    for i, text in enumerate(unique[:MAX_CARDS]):
        preview = text if len(text) <= 320 else text[:317].rstrip() + "..."
        posts.append({"index": i, "preview": preview})
    return posts


def _today_stamp():
    return datetime.now(timezone.utc).strftime("%d %b %Y")


def render_highlight_card(post):
    preview = post["preview"]
    date = _today_stamp()
    return (
        f'<a href="{PAGE_URL_FOR_LINKS}" target="_blank" rel="noopener" class="rh">\n'
        f'          <span class="rh-date">{date}</span>\n'
        f'          <span class="rh-tag">Latest &middot; From Facebook</span>\n'
        f'          <h3>Recent Activity</h3>\n'
        f'          <p>{preview}</p>\n'
        f'          <span class="rh-lnk">View on Facebook &#8599;</span>\n'
        f'        </a>\n        '
    )


def render_session_item(post):
    preview = post["preview"]
    date = _today_stamp()
    return (
        f'<a href="{PAGE_URL_FOR_LINKS}" target="_blank" rel="noopener" class="rs-item">\n'
        f'              <span class="rs-date">{date}</span>\n'
        f'              <h4>From Hon. Jonas\'s Facebook</h4>\n'
        f'              <p>{preview}</p>\n'
        f'            </a>\n            '
    )


RH_START = "<!-- AUTO-LATEST-START -->"
RH_END = "<!-- AUTO-LATEST-END -->"
RS_START = "<!-- AUTO-SESSIONS-START -->"
RS_END = "<!-- AUTO-SESSIONS-END -->"


def ensure_markers(html):
    if RH_START not in html and '<div class="rh-grid">' in html:
        html = html.replace(
            '<div class="rh-grid">',
            f'<div class="rh-grid">\n        {RH_START}\n        {RH_END}',
            1,
        )
    if RS_START not in html and '<div class="rs-list">' in html:
        html = html.replace(
            '<div class="rs-list">',
            f'<div class="rs-list">\n            {RS_START}\n            {RS_END}',
            1,
        )
    return html


def splice_cards(html, posts):
    if not posts:
        return html
    lead = posts[0]
    new_rh = f"{RH_START}\n        {render_highlight_card(lead)}{RH_END}"
    html = re.sub(
        re.escape(RH_START) + r".*?" + re.escape(RH_END),
        lambda _: new_rh,
        html,
        count=1,
        flags=re.S,
    )
    new_rs = f"{RS_START}\n            {render_session_item(lead)}{RS_END}"
    html = re.sub(
        re.escape(RS_START) + r".*?" + re.escape(RS_END),
        lambda _: new_rs,
        html,
        count=1,
        flags=re.S,
    )
    return html


def load_state():
    if not STATE_JSON.exists():
        return {}
    try:
        return json.loads(STATE_JSON.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_state(state):
    STATE_JSON.parent.mkdir(parents=True, exist_ok=True)
    STATE_JSON.write_text(
        json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def content_hash(posts):
    joined = "|".join(p["preview"] for p in posts)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def main():
    print(f"[{datetime.now(timezone.utc).isoformat()}] refresh starting")
    if not INDEX_HTML.exists():
        print(f"index.html not at {INDEX_HTML.resolve()} - aborting", file=sys.stderr)
        return 2
    posts = scrape_posts()
    print(f"scraped {len(posts)} candidate posts")
    for p in posts:
        print(f"  - {p['preview'][:80]}...")
    if not posts:
        print("no posts - leaving site unchanged (this is fine)")
        return 0
    state = load_state()
    new_hash = content_hash(posts)
    if state.get("hash") == new_hash:
        print("content unchanged since last run - no-op")
        return 0
    html = INDEX_HTML.read_text(encoding="utf-8")
    html = ensure_markers(html)
    html = splice_cards(html, posts)
    INDEX_HTML.write_text(html, encoding="utf-8")
    save_state(
        {
            "hash": new_hash,
            "posts": posts,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    print("index.html updated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
