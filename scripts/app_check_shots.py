"""Drive the live Campus Customs site in Chrome and take screenshots for output/app_check.html.

Usage: python app_check_shots.py <output_dir>
Writes PNGs plus results.json (what each screen showed + database values to compare).
"""
import json
import sys
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://localhost:5173"
OUT = Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)
results = {}


def api(path):
    with urllib.request.urlopen(BASE + path, timeout=30) as r:
        return json.load(r)


def last_reply(page):
    return page.locator(".chat-turn-assistant .chat-bubble").last.inner_text()


def ask(page, text, timeout=90_000):
    """Type a question into the chat and wait for the assistant's answer."""
    before = page.locator(".chat-turn-assistant").count()
    page.fill("#chat-input", text)
    page.click(".chat-form button[type=submit]")
    page.wait_for_function(
        "n => document.querySelectorAll('.chat-turn-assistant').length > n", arg=before, timeout=timeout
    )
    page.wait_for_timeout(700)  # let cards and animations settle


with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    ctx = browser.new_context(viewport={"width": 1920, "height": 1080}, device_scale_factor=1)
    page = ctx.new_page()

    # ---------- 1. Chat checks inventory for the item on screen ----------
    pid = "basic-hoodie-big-yale"
    db = api(f"/api/products/{pid}")
    page.goto(f"{BASE}/products/{pid}")
    page.wait_for_selector(".sizes .size")
    page.wait_for_timeout(600)
    page.locator(".sizes").screenshot(path=OUT / "inventory_sizes.png")  # before the chat covers it
    page.click("text=Ask about this item")
    page.wait_for_selector(".chat-panel")
    ask(page, "How many of these are left in medium, and what's the price?")
    page.screenshot(path=OUT / "inventory.png")
    results["inventory"] = {
        "reply": last_reply(page),
        "db_price": db["price"],
        "db_stock": {s["size"]: s["quantity"] for s in db["inventory"]},
        "page_size_M": page.locator(".size", has_text="M").first.inner_text().replace("\n", " "),
    }
    print("1 inventory:", results["inventory"]["reply"])

    # ---------- 2. Category question → dynamic cards on the page ----------
    ctx2 = browser.new_context(viewport={"width": 1920, "height": 1080}, device_scale_factor=1)
    page = ctx2.new_page()
    page.goto(f"{BASE}/")
    page.wait_for_selector(".hero")
    page.click(".chat-toggle")
    page.wait_for_selector(".chat-panel")
    ask(page, "What hoodies do you have?")
    page.wait_for_selector(".chat-results .product-card", timeout=30_000)
    page.wait_for_timeout(900)
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(300)
    page.screenshot(path=OUT / "search_cards.png")
    title = page.locator("#chat-results-title").inner_text()
    cards = page.locator(".chat-results .product-card h3").all_inner_texts()
    # Click the first chat-added card and confirm the single-item page opens.
    first_href = page.locator(".chat-results .product-card").first.get_attribute("href")
    page.locator(".chat-results .product-card").first.click()
    page.wait_for_selector(".product-detail h1")
    page.wait_for_timeout(600)
    page.click(".chat-close")
    page.wait_for_timeout(300)
    page.screenshot(path=OUT / "search_cards_click.png")
    results["search"] = {
        "reply": None,
        "panel_title": title,
        "card_count": len(cards),
        "first_cards": cards[:4],
        "first_href": first_href,
        "detail_url": page.url,
        "detail_name": page.locator(".product-detail h1").inner_text(),
        "detail_has_sizes": page.locator(".sizes .size").count(),
        "all_hoodies": all("hood" in c.lower() for c in cards),
    }
    print("2 search:", title, len(cards), "->", results["search"]["detail_url"])

    # ---------- 3. Usability (Problem 9): shop by category + size ----------
    ctx3 = browser.new_context(viewport={"width": 1440, "height": 1000}, device_scale_factor=1)
    page = ctx3.new_page()
    page.goto(f"{BASE}/products")
    page.wait_for_selector(".product-grid .product-card:not(.skeleton)")
    page.click(".filter-chip:has-text('Hoodies')")
    page.click(".size-chip:has-text('M') >> nth=0")
    page.wait_for_timeout(900)
    page.screenshot(path=OUT / "usability_filters.png")
    shown = page.locator(".product-grid .product-card h3").all_inner_texts()
    status = page.locator("p.status").first.inner_text()
    all_products = api("/api/products")
    expected = sorted(p["name"] for p in all_products if p["category"] == "Hoodies" and "M" in p["sizes_in_stock"])
    results["usability"] = {
        "url": page.url,
        "status_line": status,
        "shown_count": len(shown),
        "db_expected_count": len(expected),
        "matches_db": sorted(shown) == expected,
    }
    print("3 usability:", status, results["usability"]["matches_db"])

    # ---------- 3b. Bonus: sold-out size → "Find similar" (Problem 9 #4) ----------
    ctx4 = browser.new_context(viewport={"width": 1920, "height": 1180}, device_scale_factor=1)
    page = ctx4.new_page()
    page.goto(f"{BASE}/products/fencing-left-chest-hoodie")
    page.wait_for_selector(".find-similar")
    page.click(".find-similar:has-text('Find similar in L')")
    page.wait_for_selector(".chat-panel")
    page.wait_for_function("document.querySelectorAll('.chat-turn-assistant').length > 1", timeout=90_000)
    page.wait_for_timeout(900)
    page.evaluate("window.scrollTo(0, 0)")
    # Show the start of the reply ("L is sold out…") rather than the bottom of the cards.
    page.evaluate(
        "() => { const t = [...document.querySelectorAll('.chat-turn-user')].pop();"
        " const box = t.closest('.chat-messages');"
        " box.scrollTop += t.getBoundingClientRect().top - box.getBoundingClientRect().top - 12; }"
    )
    page.wait_for_timeout(300)
    page.screenshot(path=OUT / "usability_find_similar.png")
    alt_names = page.locator(".chat-turn-assistant").last.locator(".chat-card-name").all_inner_texts()
    alt_ok = []
    for card in page.locator(".chat-turn-assistant").last.locator("a.chat-card").all():
        alt_id = card.get_attribute("href").rsplit("/", 1)[-1]
        d = api(f"/api/products/{alt_id}")
        alt_ok.append(any(s["size"] == "L" and s["quantity"] > 0 for s in d["inventory"]))
    results["find_similar"] = {"reply": last_reply(page), "alternatives": alt_names, "all_have_L": all(alt_ok) and bool(alt_ok)}
    print("3b find similar:", alt_names, all(alt_ok))

    browser.close()

(OUT / "results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
print("saved", sorted(f.name for f in OUT.glob("*.png")))
