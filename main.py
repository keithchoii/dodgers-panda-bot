# dependencies
import aiohttp
import asyncio
import statsapi
import json
import os
import logging
from datetime import datetime, timedelta


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(),  # Console output
        logging.FileHandler('dodgers_bot.log')  # File output for debugging
    ]
)
logger = logging.getLogger(__name__)


# constants
WEBHOOK_URL = os.environ.get('DISCORD_WEBHOOK_URL')
if not WEBHOOK_URL:
    raise ValueError("DISCORD_WEBHOOK_URL environment variable is required")
HOME_GAMES_SCHEDULE = "home_games_schedule.json"
DODGERS_TEAM = {
    "name": "Los Angeles Dodgers",
    "id": 119
}


# fetch team schedule for current year from MLB API
# only stores dates of home games for the team
# IMPORTANT: this helps reduce the overall amount of API calls made each season
def get_team_schedule(team):
    # define current season
    season = datetime.now().year
    
    # check if we have already saved the schedule for this year
    # return saved schedule if it exists and is for the current year
    try:
        with open(HOME_GAMES_SCHEDULE, 'r') as f:
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
        
        # process the data to get list of dates of home games only
        team_home_dates = []
        for game in team_games:
            try:
                if game.get('home_id') == team['id'] and game.get('game_date'):
                    team_home_dates.append(game['game_date'])
            except (KeyError, TypeError) as e:
                logger.warning(f"Invalid game data structure: {e}")
                continue
        
        # check if we found any home games
        if not team_home_dates:
            logger.warning(f"No home games found for {team['name']} in {season}")
            return []
        
        # store the schedule in a json file
        schedule_data = {
            'season': season,
            'schedule': team_home_dates,
            'fetch_time': datetime.now().isoformat()
        }
        
        with open(HOME_GAMES_SCHEDULE, 'w') as f:
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


# send webhook if dodgers played a home game yesterday
# if they won, send a webhook with a coupon for a two entree plate discount from Panda Express
async def main(test_date=None):
    try:
        logger.info("Starting Dodgers win check process")
        
        # check if dodgers won their game yesterday (or test date)
        dodgers_won = yesterday_win(DODGERS_TEAM, test_date)
        
        if dodgers_won:
            logger.info("Dodgers won! Sending Discord webhook notification")
            async with aiohttp.ClientSession() as session:
                webhook_payload = {
                    "content": f"The {DODGERS_TEAM['name']} won yesterday!! Use coupon **DODGERSWIN** on online orders only at Panda Express",
                    "username": "$6 Panda"
                }
                
                try:
                    async with session.post(WEBHOOK_URL, json=webhook_payload) as resp:
                        if resp.status == 204:
                            logger.info("✅ Discord webhook sent successfully")
                        else:
                            logger.error(f"❌ Discord webhook failed with status: {resp.status}")
                            response_text = await resp.text()
                            logger.error(f"Discord API response: {response_text}")
                except Exception as e:
                    logger.error(f"❌ Error sending Discord webhook: {e}")
        else:
            logger.info("Dodgers did not play/win yesterday. No webhook notification sent.")
            
    except Exception as e:
        logger.error(f"❌ Critical error in main function: {e}")
        raise


# testing function for easier debugging
async def test_function():
    """Test the function with a known date where Dodgers won"""
    logger.info("🧪 Running in test mode")
    await main(test_date="2025-07-23")  # replace with a date you want to test


if __name__ == "__main__":
    # For testing, uncomment the line below and modify the date
    # asyncio.run(test_function())
    
    # For production, run without test_date
    asyncio.run(main())
