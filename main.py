import requests
import datetime
import logging
import os
import json

TEAM_ID = '119'  # Los Angeles Dodgers on ESPN
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
# Use env var if provided, else default to the ID you gave me
DISCORD_ROLE_ID = os.getenv("DISCORD_ROLE_ID", "1404658865756180562")
COUPON_CODE = "$6 Panda Express: https://www.pandaexpress.com"
SCHEDULE_CACHE_FILE = "schedule_cache.json"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

def pst_today():
    # PST/PDT offset approximation: GitHub Actions runs in UTC; LA is UTC-8 or UTC-7.
    # For midnight trigger we schedule 07:00 UTC which matches midnight PT.
    return (datetime.datetime.utcnow() - datetime.timedelta(hours=7)).date()

def fetch_schedule_for(date_obj):
    """Fetches and caches Dodgers schedule; returns dict for the given date (YYYY-MM-DD)."""
    target = str(date_obj)
    # Try cache
    if os.path.exists(SCHEDULE_CACHE_FILE):
        try:
            with open(SCHEDULE_CACHE_FILE, "r") as f:
                cache = json.load(f)
            if target in cache:
                return cache[target]
        except Exception as e:
            logging.warning(f"Failed reading cache: {e}")

    logging.info("Fetching fresh schedule data from ESPN...")
    url = f"https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/teams/{TEAM_ID}/schedule"
    resp = requests.get(url, timeout=20)
    resp.raise_for_status()
    data = resp.json()

    schedule = {}
    for event in data.get("events", []):
        comps = (event.get("competitions") or [{}])[0].get("competitors") or []
        date_str = (event.get("date") or "")[:10]
        home_game = False
        won = False
        for c in comps:
            if c.get("id") == TEAM_ID:
                home_game = (c.get("homeAway") == "home")
                won = bool(c.get("winner"))
        schedule[date_str] = {"home_game": home_game, "won": won}

    # Write back cache
    try:
        with open(SCHEDULE_CACHE_FILE, "w") as f:
            json.dump(schedule, f)
    except Exception as e:
        logging.warning(f"Failed writing cache: {e}")

    return schedule.get(target)

def send_webhook():
    """Send win notification to Discord, pinging the configured role if present."""
    if not DISCORD_WEBHOOK_URL:
        raise RuntimeError("DISCORD_WEBHOOK_URL is not set. Add it as a GitHub Actions secret.")

    role_mention = f"<@&{DISCORD_ROLE_ID}>" if DISCORD_ROLE_ID else ""
    content = (
        f"{role_mention} 🎉 The Dodgers won a **home game** yesterday! "
        f"Claim your {COUPON_CODE}"
    ).strip()

    payload = {
        "content": content,
        "allowed_mentions": {
            # Don't auto-parse everyone/here/roles; explicitly allow just the target role
            "parse": [],
            "roles": [DISCORD_ROLE_ID] if DISCORD_ROLE_ID else []
        }
    }

    r = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=20)
    # 204 No Content is normal for webhooks (when wait=false)
    if r.status_code not in (200, 201, 204):
        raise RuntimeError(f"Webhook failed: {r.status_code} {r.text}")
    logging.info("Webhook sent successfully.")

def main():
    try:
        yesterday = pst_today() - datetime.timedelta(days=1)
        result = fetch_schedule_for(yesterday)
        if not result:
            logging.info("No Dodgers game found for yesterday.")
            return
        if result.get("home_game") and result.get("won"):
            send_webhook()
        else:
            logging.info("Dodgers either did not play at home or did not win yesterday.")
    except Exception as e:
        logging.error(f"Error occurred: {e}")

if __name__ == "__main__":
    main()
