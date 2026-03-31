"""
Scrapers for rabbit-related search topics.
- Craigslist: scraped directly (no login needed)
- SerpAPI: used for broad web search including indexed Facebook Marketplace listings

Each scraper returns a list of result dicts with keys:
  title, url, snippet, source
"""

import requests
from bs4 import BeautifulSoup
import urllib.parse
import os
import time
import random


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

SERPAPI_KEY = os.getenv("SERPAPI_KEY", "")

# Craigslist subdomain map
CRAIGSLIST_REGIONS = {
    "Tulsa":            "tulsa",
    "Fort Smith, AR":   "fortsmith",
    "Fayetteville, AR": "fayetteville",
    "Oklahoma City":    "oklahomacity",
}


# ─── SerpAPI ─────────────────────────────────────────────────────────────────

def _serpapi_search(query: str, max_results: int = 8) -> list[dict]:
    """Search via SerpAPI (Google). Returns cleaned result dicts."""
    if not SERPAPI_KEY:
        print("[WARN] SERPAPI_KEY not set — skipping SerpAPI search.")
        return []

    results = []
    params = {
        "q": query,
        "api_key": SERPAPI_KEY,
        "num": max_results,
        "engine": "google",
        "gl": "us",
        "hl": "en",
    }

    try:
        resp = requests.get(
            "https://serpapi.com/search",
            params=params,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        for item in data.get("organic_results", [])[:max_results]:
            results.append({
                "title":   item.get("title", ""),
                "url":     item.get("link", ""),
                "snippet": item.get("snippet", "")[:300],
                "source":  urllib.parse.urlparse(item.get("link", "")).netloc.replace("www.", ""),
            })

        time.sleep(random.uniform(0.5, 1.2))

    except Exception as e:
        print(f"[WARN] SerpAPI search failed for '{query}': {e}")

    return results


# ─── Craigslist ───────────────────────────────────────────────────────────────

def _craigslist_search(subdomain: str, query: str, category: str = "sss") -> list[dict]:
    """
    Scrape Craigslist search results for a given region and query.
    category: 'sss' = all for sale, 'bab' = farm+garden, 'pet' = pets
    """
    results = []
    encoded = urllib.parse.quote_plus(query)
    url = f"https://{subdomain}.craigslist.org/search/{category}?query={encoded}&sort=date"

    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Craigslist uses a gallery/list view with <li class="cl-search-result">
        items = soup.select("li.cl-search-result")

        # Fallback for older Craigslist HTML
        if not items:
            items = soup.select(".result-row")

        for item in items[:8]:
            title_tag = (
                item.select_one("a.cl-app-anchor span.label") or
                item.select_one(".result-title") or
                item.select_one("a")
            )
            link_tag = (
                item.select_one("a.cl-app-anchor") or
                item.select_one(".result-title") or
                item.select_one("a")
            )
            price_tag = item.select_one(".priceinfo") or item.select_one(".result-price")
            meta_tag  = item.select_one(".meta") or item.select_one(".result-hood")

            if not title_tag or not link_tag:
                continue

            title   = title_tag.get_text(strip=True)
            link    = link_tag.get("href", "")
            price   = price_tag.get_text(strip=True) if price_tag else ""
            meta    = meta_tag.get_text(strip=True) if meta_tag else ""
            snippet = " · ".join(filter(None, [price, meta])) or "No details listed"

            # Make sure link is absolute
            if link.startswith("/"):
                link = f"https://{subdomain}.craigslist.org{link}"

            results.append({
                "title":   title,
                "url":     link,
                "snippet": snippet,
                "source":  f"craigslist.org ({subdomain})",
            })

        time.sleep(random.uniform(1.0, 2.0))  # polite delay

    except Exception as e:
        print(f"[WARN] Craigslist scrape failed for {subdomain} '{query}': {e}")

    return results


def _craigslist_all_regions(query: str, category: str = "sss") -> list[dict]:
    """Run a Craigslist search across all configured regions, deduped by title."""
    seen_titles = set()
    all_results = []

    for region_name, subdomain in CRAIGSLIST_REGIONS.items():
        print(f"    Craigslist {region_name}...")
        for r in _craigslist_search(subdomain, query, category):
            if r["title"] not in seen_titles:
                seen_titles.add(r["title"])
                all_results.append(r)

    return all_results


# ─── Topic scrapers ───────────────────────────────────────────────────────────

def scrape_tamuk_rabbits_for_sale(location: str, radius_miles: int) -> list[dict]:
    """
    TAMUK rabbits for sale — combines:
    - Direct Craigslist search across all 4 regions (farm+garden and pets)
    - SerpAPI for Facebook Marketplace (Google-indexed) + broader web
    """
    seen_urls = set()
    all_results = []

    # 1. Craigslist — farm+garden and pets categories
    for r in _craigslist_all_regions("TAMUK rabbit", category="bab"):
        if r["url"] not in seen_urls:
            seen_urls.add(r["url"])
            all_results.append(r)

    for r in _craigslist_all_regions("TAMUK rabbit", category="pet"):
        if r["url"] not in seen_urls:
            seen_urls.add(r["url"])
            all_results.append(r)

    # 2. SerpAPI — Google results + indexed Marketplace listings
    serp_queries = [
        f"TAMUK rabbits for sale near {location}",
        f"site:facebook.com/marketplace TAMUK rabbit Oklahoma Arkansas",
        f"Texas A&M rabbit breeder Oklahoma Arkansas for sale",
    ]
    for q in serp_queries:
        for r in _serpapi_search(q, max_results=5):
            if r["url"] not in seen_urls:
                seen_urls.add(r["url"])
                all_results.append(r)

    return all_results[:20]


def scrape_rabbit_cage_designs() -> list[dict]:
    """
    Rabbit cage design ideas — SerpAPI only (no local/Craigslist component).
    """
    seen_urls = set()
    all_results = []

    queries = [
        "rabbit cage design ideas DIY 2024",
        "rabbit hutch plans free blueprints wire floor",
        "rabbit cage stacking system ventilation design",
        "outdoor rabbit colony housing plans",
        "rabbit cage build plans meat rabbits",
    ]

    for q in queries:
        for r in _serpapi_search(q, max_results=5):
            if r["url"] not in seen_urls:
                seen_urls.add(r["url"])
                all_results.append(r)

    return all_results[:15]


def scrape_metal_rabbit_cages_for_sale() -> list[dict]:
    """
    Metal rabbit cages for sale — combines:
    - Direct Craigslist search across all 4 regions
    - SerpAPI for online retailers (Amazon, Chewy, specialty sites)
    """
    seen_urls = set()
    all_results = []

    # 1. Craigslist
    for r in _craigslist_all_regions("rabbit cage", category="bab"):
        if r["url"] not in seen_urls:
            seen_urls.add(r["url"])
            all_results.append(r)

    for r in _craigslist_all_regions("wire rabbit hutch", category="sss"):
        if r["url"] not in seen_urls:
            seen_urls.add(r["url"])
            all_results.append(r)

    # 2. SerpAPI for online retailers
    serp_queries = [
        "metal wire rabbit cage for sale buy online",
        "galvanized rabbit hutch cage 30x36 buy",
        "commercial rabbit cage stacking wire for sale",
        "site:amazon.com metal rabbit cage",
    ]
    for q in serp_queries:
        for r in _serpapi_search(q, max_results=5):
            if r["url"] not in seen_urls:
                seen_urls.add(r["url"])
                all_results.append(r)

    return all_results[:20]
