# $6 Panda Express Bot — Role Ping

This version pings a specific role when the **Dodgers win a home game** the previous day.

## Setup

1. Add a Discord webhook URL to GitHub Secrets as `DISCORD_WEBHOOK_URL`.
2. (Optional) Add `DISCORD_ROLE_ID` if you want to override the default role id.
   - Default role id used in code: `1404658865756180562`
3. Ensure the role can be mentioned:
   - **Server Settings → Roles → [Your Role] → "Allow anyone to @mention this role"** = ON (you said you've enabled this).

## Schedule

Runs daily at **12:00 AM PT** via GitHub Actions (`cron: 0 7 * * *`).

## Files

- `bot.py` — main logic (uses ESPN schedule endpoint, caches locally)
- `requirements.txt` — Python deps
- `.github/workflows/dodgers-bot.yml` — GitHub Actions workflow

## Notes

- Discord webhooks return **204 No Content** on success when `wait=false` (default).
- If the ESPN endpoint ever changes, swap to MLB Stats API easily.
- The bot only sends when the Dodgers **won at home** yesterday.
