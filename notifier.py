import argparse
import sys

from history import History
from analysis import Analysis
from coinbase import Coinbase
from slack import Slack
from stats import HourData
from constants import SlackImages

# region Argparse
parser = argparse.ArgumentParser(description="Post messages to slack if a cryptocurrency has changed price significantly")
parser.add_argument("url",
                    help="Slack incoming webhook URL")
parser.add_argument("--channel", "-c", default="",
                    help="Specify slack channel")
parser.add_argument("--name", "-n", default="Cryptocorn",
                    help="Webhook name",)
parser.add_argument("--ema", "-e", default=26, type=int,
                    help="Number of hours for EMA calculation")
parser.add_argument("-i", "--interval", default=60, type=int, choices=[5, 15, 60],
                    help="Resolution of data to fetch from coinbase (minutes)")
parser.add_argument("--threshold-ema", "-te", default=2.5, type=float,
                    help="Amount current price needs to be above/below the EMA")
parser.add_argument("--threshold-reset", "-tr", default=1.25, type=float,
                    help="Amount EMA price needs to be within last post price to reset")
parser.add_argument("--json-name", "-j",
                    help="Name of the JSON file to store with extension (use this if you're running the script multiple"
                         "times with different parameters)")
args = parser.parse_args()
# endregion

# region Constants
# Configurable Constants
EMA_THRESHOLD_PERCENT = args.threshold_ema
EMA_NUM_HOURS = args.ema
EMA_RESET_PERCENT = args.threshold_reset

BOT_NAME = args.name
SLACK_CHANNEL = args.channel

# 'Hard' Constants - may rely on other values set but shouldn't be changed
SLACK_URL = args.url

if args.json_name is not None:
    DATA_FILE = args.json_name
else:
    DATA_FILE = "last_post_data.json"

Coinbase.interval = args.interval
# endregion

# Get data and convert accordingly
cb = Coinbase()
cur_price = cb.latest_price()
prices = cb.price_list()

# Get history from last runs, use it to work out what test to make
history = History(DATA_FILE)

# Get stats from coinbase data
# If change isn't large enough, then update history and exit
stats = HourData(prices, EMA_NUM_HOURS)
if Analysis.ema_checks(stats, history, EMA_THRESHOLD_PERCENT, EMA_RESET_PERCENT):
    sys.exit(1)

if not Analysis.should_post(history, stats, prices, EMA_THRESHOLD_PERCENT):
    sys.exit(1)

print("Posting to slack")
attachments = Slack.generate_attachment(prices, stats, EMA_NUM_HOURS)
image_url = SlackImages.get_image(stats.is_diff_positive)
Slack.post_to_slack(BOT_NAME, image_url, "", attachments, SLACK_URL, SLACK_CHANNEL)

history.price = stats.cur_price
history.rising = stats.is_diff_positive
history.ema_reset = False
history.save()

print("Done")
