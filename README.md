# $6 Panda Express Bot

A simple Discord bot that supports your Panda Express addiction and notifies you when their [Dodgers discount](https://www.pandaexpress.com/promo/dodgerswin) is usable

## Self Setup on GitHub

You want to use this bot? Go ahead idc, but you have to set it up yourself (it's free dw)

### 1. Fork/Clone this Repository

Easier way is to fork the repository, but if you know what you're doing you can clone it too I guess

### 2. Set up GitHub Secrets

This is IMPORTANT, the bot needs to know which channel to send its messages. You have the option to have it ping a specific role as well. Make sure you can locate this

Go to your repository Settings → Secrets and variables (under Security) → Actions → Secrets → New repository secret. Copy the following names that look `LIKE_THIS` into name, and your personal information into the value under it:

- `DISCORD_WEBHOOK_URL`: Your Discord webhook URL. To obtain this go to Server Settings > Integrations (under Apps) > Webhooks > Create/New Webhook.
- `DISCORD_ROLE_ID`: Choose a role that you want pinged (OPTIONAL). To obtain this go to Server Settings > Roles (under People) > Find your designated role and click the three dots (says More when hovered) > Copy Role ID.

Once you add a secret, you can't see what your secret is ever again (unless Github changes this), but you can always go back and edit the secret with a new value.

### 3. You did it :tada:

The bot should now automatically run daily at 12AM PST (-8 UTC). You can also manually trigger it or even test it from the Actions tab on your repository. If something isn't working, check below. Otherwise, enjoy your Panda

## Troubleshooting

- If the bot stops working, check the Actions logs for errors
- Verify your Discord webhook URL is valid
- Ensure the MLB API is accessible and working
- Check that the Dodgers team ID on the API is still correct (119)
- Ask chatGPT?

## Problems/Suggestions

If you have any issues and the troubleshooting didn't help, you encountered any bugs, or you want to suggest changes that improve the bot, just go to the Issues tab and create a new Issue. I'm not sure how often I will end up checking on this but I will try.