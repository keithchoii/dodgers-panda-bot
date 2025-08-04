# $6 Panda Express Bot

A Discord bot that checks if the Los Angeles Dodgers won their home game yesterday and sends a notification message with a Panda Express coupon code.

## Features

- Checks Dodgers home game results daily at 12AM PST
- Sends Discord webhook with coupon code when Dodgers win
- Caches team schedule to reduce API calls
- Logging for handling and debugging errors
- Runs serverless via GitHub Actions

## Self Setup on GitHub

### 1. Fork/Clone this Repository

### 2. Set up GitHub Secrets

Go to your repository Settings → Secrets and variables → Actions, then add:

- `DISCORD_WEBHOOK_URL`: Your Discord webhook URL. To obtain this go to Server Settings > Integrations (under Apps) > Webhooks > Create/New Webhook.

### 3. Configure the Workflow

The GitHub Actions workflow will automatically run daily at 12AM PST. You can also manually trigger it from the Actions tab.

## Local Development

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Run Locally
```bash
python main.py
```

### Test with Specific Date
```bash
# Edit main.py and uncomment the test line
python main.py
```

## Troubleshooting

- If the bot stops working, check the Actions logs
- Verify your Discord webhook URL is correct
- Ensure the MLB API is accessible
- Check that the Dodgers team ID is still valid (119)