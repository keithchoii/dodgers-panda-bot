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


# constants
WEBHOOK_URL = os.environ.get('DISCORD_WEBHOOK_URL')  # this is REQUIRED
if not WEBHOOK_URL:
    raise ValueError("DISCORD_WEBHOOK_URL environment variable is required")
ROLE_ID = os.environ.get('DISCORD_ROLE_ID')  # this is optional
SCHEDULE_FILE = "home_games_schedule.json"  # determine where the schedule is cached
DODGERS_TEAM = {
    "name": "Los Angeles Dodgers",  
    "id": 119
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
                return saved_schedule['schedule']
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
        
        # process the data to get list of home games only
        team_home_games = []
        for game in team_games:
            try:
                if game.get('home_id') == team['id'] and game.get('game_date'):
                    team_home_games.append(game)
            except (KeyError, TypeError) as e:
                logger.warning(f"Invalid game data structure: {e}")
                continue
        
        # check if we found any home games
        if not team_home_games:
            logger.warning(f"No home games found for {team['name']} in {season}")
            return []
        
        # store the schedule in a json file
        schedule_data = {
            'season': season,
            'schedule': team_home_games,
            'fetch_time': datetime.now().isoformat()
        }
        
        with open(SCHEDULE_FILE, 'w') as f:
            json.dump(schedule_data, f, indent=2)
        
        logger.info(f"Successfully fetched and cached schedule for {team['name']} in {season} ({len(team_home_dates)} home games)")
        return schedule_data['schedule']
        
    except Exception as e:
        logger.error(f"Error fetching {team['name']} schedule from MLB API: {e}")
        return None


# check if the given team won yesterday
def yesterday_win(team, test_date=None):
    try:
        # get list of team's schedule
        schedule = get_team_schedule(team)
        
        # get yesterday's date or use test date
        if test_date:
            target_date = test_date
            logger.info(f"Running in test mode with date: {target_date}")
        else:
            target_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            logger.info(f"Checking game result for date: {target_date}")
        
        # check if team played on target date
        if target_date not in schedule:
            logger.info(f"No home game found for {team['name']} on {target_date}")
            return False
        
        # get game result for the team on target date
        try:
            games = statsapi.schedule(date=target_date, team=team['id'])
            
            if not games:
                logger.warning(f"No games found for {team['name']} on {target_date}")
                return False
            
            game = games[0]  # get the first (and should be only) game
            
        except Exception as e:
            logger.error(f"Error fetching game data for {team['name']} on {target_date} from MLB API: {e}")
            return False
        
        # check if game is final and team won
        if game.get('status') == 'Final':
            winning_team = game.get('winning_team', '')
            if winning_team == team['name']:
                logger.info(f"{team['name']} WON on {target_date}!")
                return True
            else:
                logger.info(f"{team['name']} lost on {target_date}. Winner: {winning_team}")
                return False
        else:
            logger.info(f"Game on {target_date} is not final yet. Status: {game.get('status')}")
            return False
        
    except Exception as e:
        logger.error(f"Error checking game for {team['name']}: {e}")
        return False


# get game details for a team on a specific date (home games optimized)
def get_game_details(team, target_date):
    try:
        # get list of team's schedule
        schedule = get_team_schedule(team)

        # if no home game exists on date
        if target_date not in schedule:
            return {
                'date': target_date,
                'played_home_game': False,
                'status': 'No Home Game',
            }

        games = statsapi.schedule(date=target_date, team=team['id'])
        if not games:
            return {
                'date': target_date,
                'played_home_game': True,
                'status': 'No Data',
            }

        game = games[0]
        status = game.get('status')
        is_final = status == 'Final'
        home_name = game.get('home_name', '')
        away_name = game.get('away_name', '')
        home_score = game.get('home_score')
        away_score = game.get('away_score')
        winning_team = game.get('winning_team', '')

        is_home = home_name == team['name']
        opponent = away_name if is_home else home_name

        return {
            'date': target_date,
            'played_home_game': True,
            'status': status,
            'is_final': is_final,
            'is_home': is_home,
            'team_name': team['name'],
            'opponent_name': opponent,
            'team_score': home_score if is_home else away_score,
            'opponent_score': away_score if is_home else home_score,
            'winning_team': winning_team,
        }
    except Exception as e:
        logger.error(f"Error getting game details: {e}")
        return {
            'date': target_date,
            'played_home_game': False,
            'status': 'Error',
        }


# build a Discord webhook payload from game details
def build_webhook_payload(team, test_date=None):
    try:
        # get list of team's schedule
        schedule = get_team_schedule(team)


    
    date_str = game_info.get('date', '')
    status = game_info.get('status', 'Unknown')

    if status == 'No Home Game':
        content = f"No Dodgers home game on {date_str}."
        return { 'content': content }

    if status in ('Error', 'No Data'):
        content = f"Could not retrieve Dodgers game details for {date_str} (status: {status})."
        return { 'content': content }

    team_name = game_info.get('team_name')
    opponent = game_info.get('opponent_name')
    team_score = game_info.get('team_score')
    opponent_score = game_info.get('opponent_score')
    is_final = game_info.get('is_final', False)
    winning_team = game_info.get('winning_team')

    if is_final:
        result = 'W' if winning_team == team_name else 'L'
        title = f"{team_name} vs {opponent} — Final ({date_str})"
        description = f"Final Score: {team_name} {team_score} - {opponent_score} {opponent} ({result})"
    else:
        title = f"{team_name} vs {opponent} — {status} ({date_str})"
        description = f"Current/Latest Score: {team_name} {team_score} - {opponent_score} {opponent}"

    embed = {
        'title': title,
        'description': description,
    }

    return { 'embeds': [embed] }


# send message as bot on Discord
# WARNING: check if payload format is valid
async def send_webhook(payload):
    async with aiohttp.ClientSession() as session:
        try:
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
        logger.info("Good morning! Daily Dodgers game check process starting...")
        target_date = test_date if test_date else (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        game_info = get_game_details(DODGERS_TEAM, target_date)
        payload = build_webhook_payload(game_info)
        await send_webhook(payload)
    except Exception as e:
        logger.error(f"❌ Critical error in main function: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
