# 🐇 Rabbit Scout

Automated daily email digest that scrapes the web for rabbit-related topics and
delivers them to your inbox in three scheduled emails per day.

## Topics Covered

| # | Topic | What it searches |
|---|-------|-----------------|
| 1 | **TAMUK Rabbits for Sale** | Breeders and listings within 180 miles of Braggs, OK |
| 2 | **Rabbit Cage Designs** | DIY plans, blueprints, design ideas |
| 3 | **Metal Rabbit Cages for Sale** | Wire/galvanized cages available to buy online |

## Email Schedule

| Period | Time |
|--------|------|
| 🌅 Morning | 7:00 AM |
| ☀️ Afternoon | 12:00 PM |
| 🌙 Evening | 6:00 PM |

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure your credentials

Copy the example env file and fill it in:

```bash
cp ..env.example ..env
nano ..env   # or open in any text editor
```

Fill in:
```
GMAIL_ADDRESS=your_email@gmail.com
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx
RECIPIENT_EMAIL=your_email@gmail.com
SEARCH_LOCATION=Braggs, OK
SEARCH_RADIUS_MILES=180
```

### 3. Get a Gmail App Password

You need a Google App Password (not your regular Gmail password):

1. Go to https://myaccount.google.com/security
2. Enable **2-Step Verification** if not already on
3. Search for "App passwords" → Create one named "Rabbit Scout"
4. Copy the 16-character password into `.env` as `GMAIL_APP_PASSWORD`

---

## Running

### Test it immediately
```bash
# Send a morning digest right now
python rabbit_scout.py --now morning

# Or afternoon / evening
python rabbit_scout.py --now afternoon
python rabbit_scout.py --now evening
```

### Schedule with Cron (Linux/Mac — recommended)

Open your crontab:
```bash
crontab -e
```

Add these three lines (update the path to match where you put the project):
```cron
0 7  * * * cd /home/ashley/rabbit_scout && python rabbit_scout.py --now morning  >> rabbit_scout.log 2>&1
0 12 * * * cd /home/ashley/rabbit_scout && python rabbit_scout.py --now afternoon >> rabbit_scout.log 2>&1
0 18 * * * cd /home/ashley/rabbit_scout && python rabbit_scout.py --now evening  >> rabbit_scout.log 2>&1
```

### Schedule with Task Scheduler (Windows)

1. Open **Task Scheduler** → Create Basic Task
2. Set trigger: **Daily** at 7:00 AM
3. Action: Start a program
   - Program: `python`
   - Arguments: `C:\path\to\rabbit_scout\rabbit_scout.py --now morning`
   - Start in: `C:\path\to\rabbit_scout\`
4. Repeat for 12:00 PM (`--now afternoon`) and 6:00 PM (`--now evening`)

### Alternatively: Run as a persistent background process
```bash
# Runs the scheduler forever in the background
nohup python rabbit_scout.py >> rabbit_scout.log 2>&1 &
```

---

## Project Structure

```
rabbit_scout/
├── rabbit_scout.py         # Main runner + scheduler
├── requirements.txt
├── .env.example            # Copy to .env and fill in
├── .env                    # Your credentials (never commit this)
├── scrapers/
│   └── search.py           # Web scraping logic for all 3 topics
└── utils/
    └── emailer.py          # HTML email builder and Gmail sender
```

---

## Adding New Topics

To add a new search topic:

1. Add a new function in `scrapers/search.py` following the existing pattern
2. Call it in `rabbit_scout.py` inside `run_digest()`
3. Add a section in `utils/emailer.py` in `build_email_html()`

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `Missing .env values` | Copy `.env.example` to `.env` and fill it in |
| Gmail auth error | Double-check your App Password; make sure 2FA is enabled |
| No results showing | Bing may have rate-limited — wait a few minutes and retry |
| Emails going to spam | Add your Gmail address to your contacts |
