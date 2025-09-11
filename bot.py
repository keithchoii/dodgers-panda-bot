# dependencies
import asyncio
import aiohttp
import statsapi
import json
import os
import logging
from datetime import datetime, timedelta


# configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(),  # console output
        logging.FileHandler('dodgers_bot.log')  # file output for debugging
    ]
)
logger = logging.getLogger(__name__)


## CONSTANTS
# github secrets
WEBHOOK_URL = os.environ.get('DISCORD_WEBHOOK_URL')
if not WEBHOOK_URL:
    raise ValueError("DISCORD_WEBHOOK_URL environment variable is required")  # this is REQUIRED
ROLE_ID = os.environ.get('DISCORD_ROLE_ID')  # this is optional
# file locations
MESSAGE_CONTENTS = "message_contents.json"  # webhook contents
SCHEDULE_FILE = "home_games_schedule.json"  # determine where the schedule is cached
# team data
DODGERS_TEAM = {
    'name': "Los Angeles Dodgers",  
    'id': 119
}


# fetch team schedule for current year from MLB API
# IMPORTANT: only stores schedule of home games for the team
def get_team_schedule(team):
    # define current season
    season = datetime.now().year
    
    # check if we have already saved the schedule for this year
    # return saved schedule if it exists and is for the current year
    try:
        with open(SCHEDULE_FILE, 'r') as f:
            saved_schedule = json.load(f)
            if saved_schedule.get('season') == season:
                logger.info(f"Using cached schedule for {team['name']} in {season}")
                return saved_schedule.get('games')
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        logger.info("No valid cached schedule found, fetching fresh data from MLB API")
    
    # fetch schedule from MLB API
    logger.info(f"Fetching {team['name']} schedule for {season} from MLB API")
    try:
        # get list of games for Dodgers in current year
        team_games = statsapi.schedule(team=team['id'], season=season)
        
        # check if API call was successful
        if not team_games:
            logger.error(f"Failed to obtain games for {team['name']} in {season} from MLB API")
            return None
        
        # process the data to get list of home games and their relevant info
        team_home_games = []
        for game in team_games:
            try:
                if game.get('home_id') == team['id'] and game.get('game_date'):
                    team_home_games.append({
                        'game_id': game.get('game_id'),
                        'game_date': game.get('game_date'),
                        'home_id': game.get('home_id'),
                        'home_name': game.get('home_name'),
                        'away_id': game.get('away_id'),
                        'away_name': game.get('away_name'),
                        # initialize below fields as empty, fill in later after the games are played
                        'status': game.get('status'),
                        'home_score': None,
                        'away_score': None,
                        'winning_team': None
                    })
            except (KeyError, TypeError) as e:
                logger.warning(f"Invalid game data structure: {e}")
                continue
        
        # check if home games exist
        if not team_home_games:
            logger.warning(f"No home games found for {team['name']} in {season}")
            return []
        
        # store the schedule in a json file
        schedule_data = {
            'season': season,
            'games': team_home_games,
            'fetch_time': datetime.now().isoformat()
        }
        
        with open(SCHEDULE_FILE, 'w') as f:
            json.dump(schedule_data, f, indent=2)
        
        logger.info(f"Successfully fetched and cached schedule for {team['name']} in {season} ({len(team_home_games)} home games)")
        return schedule_data['games']
        
    except Exception as e:
        logger.error(f"Error fetching {team['name']} schedule from MLB API: {e}")
        return None
        

# get game details for a home game played by a team on a specific date
def get_game_details(team, target_date):
    try:
        # get team's schedule
        schedule = get_team_schedule(team)
        if not schedule:
            logger.info(f"No schedule found for {team['name']}")
            return None

        # check if there is home game on target date
        target_game = next((g for g in schedule
                     if g.get('game_date') == target_date and g.get('home_id') == team['id']), None)
        if not target_game:
            logger.info(f"No home game found for {team['name']} on {target_date}")
            return None

        status = target_game.get('status')
        home_score = target_game.get('home_score')
        away_score = target_game.get('away_score')
        winning_team = target_game.get('winning_team')
        game_id = target_game.get('game_id')

        # check schedule if game was recorded
        # otherwise retrieve results from API
        if status != 'Final' or home_score is None or away_score is None:
            try:
                games_list = statsapi.schedule(date=target_date, team=team['id'])
                game = next((g for g in games_list if g.get('game_id') == game_id), None)
                if game:
                    status = game.get('status', status)
                    home_score = game.get('home_score', home_score)
                    away_score = game.get('away_score', away_score)
                    winning_team = game.get('winning_team', winning_team)

                # if any data is missing, make necessary API calls
                if status != 'Final' or home_score is None or away_score is None:
                    try:
                        linescore = statsapi.get('game_linescore', {'gamePk': game_id})
                        home_score = linescore.get('teams', {}).get('home', {}).get('runs', home_score)
                        away_score = linescore.get('teams', {}).get('away', {}).get('runs', away_score)
                    except Exception:
                        pass

                    try:
                        g = statsapi.get('game', {'gamePk': game_id})
                        status = (
                            g.get('status', {}).get('detailedState')
                            or g.get('status', {}).get('abstractGameState')
                            or status
                        )
                    except Exception:
                        pass

                if status == 'Final' and home_score is not None and away_score is not None and not winning_team:
                    winning_team = target_game.get('home_name') if home_score > away_score else target_game.get('away_name')

                # persist back into cache
                target_game['status'] = status
                target_game['home_score'] = home_score
                target_game['away_score'] = away_score
                target_game['winning_team'] = winning_team

                # write-through cache
                try:
                    with open(SCHEDULE_FILE, 'r') as f:
                        data = json.load(f)
                    # replace the entries (note: cache root key is 'games')
                    for i, g in enumerate(data.get('games', [])):
                        if g.get('game_date') == target_date and g.get('home_id') == team['id']:
                            data['games'][i] = target_game
                            break
                    with open(SCHEDULE_FILE, 'w') as f:
                        json.dump(data, f, indent=2)
                except Exception:
                    pass
            except Exception:
                pass

        return {
            'home_team': target_game.get('home_name'),
            'away_team': target_game.get('away_name'),
            'home_score': home_score,
            'away_score': away_score,
            'winning_team': winning_team,
        }

    except Exception as e:
        logger.error(f"Error getting game details: {e}")
        return None


# build a Discord webhook payload for the Dodgers
def build_webhook_payload(game_info):
    try:
        # if no game info (None), write an empty JSON object
        if not game_info:
            with open(MESSAGE_CONTENTS, 'w') as f:
                json.dump({}, f)
            return

        home_team = game_info.get('home_team')
        away_team = game_info.get('away_team')
        home_score = game_info.get('home_score')
        away_score = game_info.get('away_score')
        winning_team = game_info.get('winning_team')

        # check if home team won
        home_win = winning_team == home_team

        # configure role ping if exists
        role_ping = f"<@&{ROLE_ID}> " if ROLE_ID else ""

        # message contents
        embed_title = f"Extras"
        embed_description = ""
        embed_color = 23196  # this is Dodger Blue
        score_field = {
            'name': "Final Score",
            'value': f"**{home_team}** {home_score} - {away_score} **{away_team}**\n\nWinner: **{winning_team}**"
        }
        promo_field = {
            'name': "What is the promo?",
            'value': "This is a [collab](https://www.pandaexpress.com/promo/dodgerswin) between Panda Express and the LA Dodgers. Get the Panda Express mobile app to use the promo code, it's the only way.\n\nNot sponsored btw, and if you want to join in on the bigback activites get someone to give you the role for ping"
        }
        website_field = {
            'name': "Website Tracker",
            'value': "Check out [this website](https://www.ispandasix.com/) for a website tracker, it also shows the next upcoming games so you can plan for it\n\nThe creator of the website didn't make me (the bot) but they inspired my creation so big shoutout"
        }

        # different messages on win/loss
        if home_win:
            payload = {
                'content': f"THE {home_team} WON YESTERDAY :tada: {role_ping}come get your $6 plate :fortune_cookie:\n\nUse code: **DODGERSWIN**\n\nNot sure where? Check the links below\n_ _",
                'embeds': [
                    {
                        'title': embed_title,
                        'description': embed_description,
                        'color': embed_color,
                        'fields': [
                            score_field,
                            promo_field,
                            website_field
                        ]
                    }
                ]
            }
        else:
            payload = {
                'content': f"The {home_team} played yesterday but they lost\n\nNo big back activities today :frowning:",
                'embeds': [
                    {
                        'title': embed_title,
                        'description': embed_description,
                        'color': embed_color,
                        'fields': [
                            score_field,
                            website_field
                        ]
                    }
                ]
            }
        
        with open(MESSAGE_CONTENTS, 'w') as f:
            json.dump(payload, f, indent=2)

    except Exception as e:
        logger.error(f"Error building webhook payload: {e}")
        # on error, write empty object to avoid sending a bad payload
        try:
            with open(MESSAGE_CONTENTS, 'w') as f:
                json.dump({}, f)
        except Exception:
            pass


# send message as a bot on Discord
async def send_webhook():
    async with aiohttp.ClientSession() as session:
        try:
            # read payload from file
            try:
                with open(MESSAGE_CONTENTS, 'r') as f:
                    payload = json.load(f)
            except FileNotFoundError:
                logger.info("No message file found; skipping webhook send")
                return
            except json.JSONDecodeError:
                logger.error("Message file is invalid JSON; skipping webhook send")
                return

            # check if message is empty
            if not payload:
                logger.info("No message contents, no home game played yesterday; skipping webhook send")
                return

            # send webhook
            async with session.post(WEBHOOK_URL, json=payload) as resp:
                if resp.status == 204:
                    logger.info("✅ Discord webhook sent successfully")
                else:
                    logger.error(f"❌ Discord webhook failed with status: {resp.status}")
                    response_text = await resp.text()
                    logger.error(f"Discord API response: {response_text}")
        except Exception as e:
            logger.error(f"❌ Error sending Discord webhook: {e}")


# check conditions for Panda x Dodgers collab discount and send webhook
async def main(test_date=None):
    try:
        logger.info("Daily Dodgers game check process starting...")
        target_date = test_date if test_date else (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        build_webhook_payload(get_game_details(DODGERS_TEAM, target_date))
        await send_webhook()
    except Exception as e:
        logger.error(f"❌ Critical error in main function: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
