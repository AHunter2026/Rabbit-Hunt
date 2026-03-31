"""
rabbit_scout.py — Main runner for Rabbit Scout digest emails.

Run modes:
  python rabbit_scout.py --now morning   # send immediately (for testing)
  python rabbit_scout.py --now afternoon
  python rabbit_scout.py --now evening
  python rabbit_scout.py                 # run scheduler (for cron: call once at boot)

Cron setup (runs scheduler forever — add to crontab):
  @reboot cd /path/to/rabbit_scout && python rabbit_scout.py >> rabbit_scout.log 2>&1 &

OR use three separate cron jobs (simpler — recommended):
  0 7  * * * cd /path/to/rabbit_scout && python rabbit_scout.py --now morning  >> rabbit_scout.log 2>&1
  0 12 * * * cd /path/to/rabbit_scout && python rabbit_scout.py --now afternoon >> rabbit_scout.log 2>&1
  0 18 * * * cd /path/to/rabbit_scout && python rabbit_scout.py --now evening  >> rabbit_scout.log 2>&1
"""

import os
import sys
import argparse
import schedule
import time
from datetime import datetime
from dotenv import load_dotenv

# Load .env from ..env file in same directory as this script
script_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(script_dir, ".env"))

from scrapers.search import (
    scrape_tamuk_rabbits_for_sale,
    scrape_rabbit_cage_designs,
    scrape_metal_rabbit_cages_for_sale,
)
from utils.emailer import build_email_html, send_email


# ─── Config from ..env ────────────────────────────────────────────────────────

GMAIL_ADDRESS     = os.getenv("GMAIL_ADDRESS", "")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
RECIPIENT_EMAIL   = os.getenv("RECIPIENT_EMAIL", "")
SEARCH_LOCATION   = os.getenv("SEARCH_LOCATION", "Braggs, OK")
SEARCH_RADIUS     = int(os.getenv("SEARCH_RADIUS_MILES", "180"))


# ─── Core job ────────────────────────────────────────────────────────────────

def run_digest(period: str):
    """Scrape all topics and send the digest email for the given period."""
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M')}] Starting {period} digest...")

    print("  Scraping TAMUK rabbits for sale...")
    tamuk = scrape_tamuk_rabbits_for_sale(SEARCH_LOCATION, SEARCH_RADIUS)
    print(f"    → {len(tamuk)} results")

    print("  Scraping rabbit cage designs...")
    cage_designs = scrape_rabbit_cage_designs()
    print(f"    → {len(cage_designs)} results")

    print("  Scraping metal rabbit cages for sale...")
    metal_cages = scrape_metal_rabbit_cages_for_sale()
    print(f"    → {len(metal_cages)} results")

    subject_labels = {
        "morning":   "🌅 Morning",
        "afternoon": "☀️ Afternoon",
        "evening":   "🌙 Evening",
    }
    subject = (
        f"{subject_labels.get(period, period.title())} Rabbit Scout — "
        f"{datetime.now().strftime('%b %d, %Y')}"
    )

    html = build_email_html(
        tamuk_results=tamuk,
        cage_design_results=cage_designs,
        metal_cage_results=metal_cages,
        location=SEARCH_LOCATION,
        radius=SEARCH_RADIUS,
        period=period,
    )

    success = send_email(
        html_body=html,
        subject=subject,
        gmail_address=GMAIL_ADDRESS,
        gmail_app_password=GMAIL_APP_PASSWORD,
        recipient=RECIPIENT_EMAIL,
    )

    if not success:
        print(f"[ERROR] {period.title()} digest failed to send.")
    else:
        print(f"[DONE] {period.title()} digest sent successfully.")


# ─── Scheduler ───────────────────────────────────────────────────────────────

def start_scheduler():
    """Set up and run the daily schedule."""
    print("Rabbit Scout scheduler starting...")
    print(f"  Morning:   07:00")
    print(f"  Afternoon: 12:00")
    print(f"  Evening:   18:00")
    print(f"  Location:  {SEARCH_LOCATION} ({SEARCH_RADIUS} mi radius)")
    print()

    schedule.every().day.at("07:00").do(run_digest, period="morning")
    schedule.every().day.at("12:00").do(run_digest, period="afternoon")
    schedule.every().day.at("18:00").do(run_digest, period="evening")

    while True:
        schedule.run_pending()
        time.sleep(30)


# ─── Entry point ─────────────────────────────────────────────────────────────

def validate_config():
    missing = []
    if not GMAIL_ADDRESS:      missing.append("GMAIL_ADDRESS")
    if not GMAIL_APP_PASSWORD: missing.append("GMAIL_APP_PASSWORD")
    if not RECIPIENT_EMAIL:    missing.append("RECIPIENT_EMAIL")
    if missing:
        print(f"[ERROR] Missing required ..env values: {', '.join(missing)}")
        print("  Copy ..env.example to ..env and fill in your credentials.")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rabbit Scout digest emailer")
    parser.add_argument(
        "--now",
        choices=["morning", "afternoon", "evening"],
        help="Send a digest immediately (for testing or manual runs)",
    )
    args = parser.parse_args()

    validate_config()

    if args.now:
        run_digest(period=args.now)
    else:
        start_scheduler()
