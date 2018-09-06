import sys
import argparse

from coinbase import Coinbase, Currency
from history import History
from misc import *
from slack import Slack
from stats import TimeIntervalData

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
parser.add_argument("--threshold", "-t", default=2.5, type=float,
                    help="Amount current price needs to be above EMA")
parser.add_argument("--cooldown", "-cd", default=6, type=int,
                    help="Number of hours to wait before reposting")
parser.add_argument("--json-name", "-j",
                    help="Name of the JSON file to store with extension (use this if you're running the script multiple"
                         "times with different parameters)")
args = parser.parse_args()
# endregion

# region Constants
# Configurable Constants
EMA_THRESHOLD_PERCENT = args.threshold
EMA_NUM_HOURS = args.ema
HOURS_BETWEEN_POSTS = args.cooldown

class SlackColourThresholds:
    GOOD = 1
    NEUTRAL = 0
    WARNING = -1

PRICE_UP_IMAGE = "https://i.imgur.com/2PVZ0l1.png"
PRICE_DOWN_IMAGE = "https://i.imgur.com/21sDn3D.png"
BOT_NAME = args.name
SLACK_CHANNEL = args.channel

# 'Hard' Constants - may rely on other values set but shouldn't be changed
SLACK_URL = args.url

if args.json_name is not None:
    DATA_FILE = args.json_name
else:
    DATA_FILE = "last_post_data.json"
# endregion

# Get data and convert accordingly
cb = Coinbase()
cur_price = cb.latest_price()
prices = cb.price_list()

# Get history from last runs, use it to work out what test to make
history = History(DATA_FILE)

# Get stats from coinbase data
# If change isn't large enough, then update history and exit
stats = TimeIntervalData(prices, EMA_NUM_HOURS)
if stats.ema_percent_diff_positive < EMA_THRESHOLD_PERCENT:
    print(f"Current price not outside threshold ({stats.formatted_info()})")
    history.ema_reset = True
    history.save()
    sys.exit(1)

print(f"Current price is outside threshold difference ({stats.formatted_info()})")

if not should_post(history, stats, EMA_THRESHOLD_PERCENT):
    sys.exit(1)

# region Generate slack info
stats_1_hour = TimeIntervalData(prices, EMA_NUM_HOURS, 1)
stats_24_hour = TimeIntervalData(prices, EMA_NUM_HOURS, 24)
stats_7_day = TimeIntervalData(prices, EMA_NUM_HOURS, 24 * 7)

sign_str = "up" if stats.diff_positive else "down"
attachment_pretext = f"{Currency.PRIMARY_CURRENCY_LONG}'s price has gone {sign_str}. Current price: {Currency.SECONDARY_CURRENCY_SYMBOL}{stats.cur_price:,.0f}"
image_url = PRICE_UP_IMAGE if stats.diff_positive else PRICE_DOWN_IMAGE

# noinspection PyListCreation
attachments = []
attachments.append(format_stat(stats_1_hour, stats, "Price 1 hour ago:      ", attachment_pretext))
attachments.append(format_stat(stats_24_hour, stats, "Price 24 hours ago:  "))
attachments.append(format_stat(stats_7_day, stats, "Price 7 days ago:      "))
# endregion

print("Posting to slack")
Slack.post_to_slack(BOT_NAME, image_url, "", attachments, SLACK_URL, SLACK_CHANNEL)

history.save()

print("Done")

