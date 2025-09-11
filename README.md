# $6 Panda Express Bot

A simple Discord bot that supports your Panda Express addiction and notifies you when their [Dodgers discount](https://www.pandaexpress.com/promo/dodgerswin) is usable

## Self Setup on GitHub

You want to use this bot? Go ahead idc, but you have to set it up yourself (it's free dw)

### 1. Fork/Clone this Repository

Easier way is to fork the repository, but if you know what you're doing you can clone it too I guess

### 2. Set up GitHub Secrets

This is IMPORTANT, the bot needs to know which channel to send its messages to. Make sure you add the necessary secrets!

Go to your repository Settings → Secrets and variables (under Security) → Actions → Secrets → New repository secret. Copy the following names that look `LIKE_THIS` into the Name section, and your personal information into the Secret section under it:

- `DISCORD_WEBHOOK_URL`: To obtain this go to Server Settings > Integrations (under Apps) > Webhooks > Create/New Webhook > Copy Webhook URL. After, customize your bot's name as you like and choose the channel you want the messages to appear in!

**(OPTIONAL)** Secrets:

- `DISCORD_ROLE_ID`: To obtain this go to Server Settings > Roles (under People) > Find your designated role and click the three dots (says More when hovered) > Copy Role ID. Now the bot will ping this role when it sends its messages!
- `HEALTH_WEBHOOK_URL`: To obtain this follow the same instructions as above. Add this secret if you want to be notified when the bot fails.
- `TEST_WEBHOOK_URL`: To obtain this follow the same instructions as above. Add this secret if you need to test using the built-in Debug workflow on Github.

Once you add a secret you can't see what your secret is ever again, but you can always go back and edit the secret with a new value.

### 3. You did it :tada:

The bot should now automatically run daily at 12AM PST (-8 UTC). You can also manually trigger it or even test it from the Actions tab on your repository. If something isn't working, check below. Otherwise, enjoy your Panda :smile:

## Troubleshooting

- If the bot stops working, check the Actions logs for errors
- Verify your Discord webhook URLs are valid
- Ensure the MLB API is accessible and working
- Check that the Dodgers team ID on the API is still correct (119)
- Ask AI?

## Problems/Suggestions

If you have any issues and the troubleshooting didn't help, you encountered any bugs, or you want to suggest changes that improve the bot, go to [Issues](https://github.com/keithchoii/dodgers-panda-bot/issues)
 
### Copyright

This bot is not affiliated with the Los Angeles Dodgers or Panda Express. Game data is retrieved from MLB Stats API through [statsapi](https://github.com/toddrob99/MLB-StatsAPI)