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

history = History(DATA_FILE)

# Check whether to update
stats = TimeIntervalData(prices, EMA_NUM_HOURS)
if stats.ema_percent_diff_positive < EMA_THRESHOLD_PERCENT:
    print(f"Current price not outside threshold ({stats.formatted_info()})")
    sys.exit(1)
else:
    print(f"Current price increased above threshold difference ({stats.formatted_info()})")

# region Last post checks
# If magnitude is opposite then include anyway
if history.rising != stats.diff_positive:
    print(f"Last change was in the opposite direction")
    sys.exit(1)

# Allow if increase is greater again
if history.rising:
    required_perc_diff = (1 + EMA_THRESHOLD_PERCENT / 100)
    threshold_sign_str = "above"
else:
    required_perc_diff = (1 - EMA_THRESHOLD_PERCENT / 100)
    threshold_sign_str = "below"

new_threshold = history.price * required_perc_diff
print(f"To repost within the cooldown period the current price must be {threshold_sign_str}: {new_threshold:.0f}")
if (history.rising and stats.cur_price > new_threshold) or \
        (not history.rising and stats.cur_price < new_threshold):
    print(f"Beats new threshold price ({stats.cur_price:.0f}/{new_threshold:.0f})")
    sys.exit(1)

print(f"Does not beat new threshold price: ({stats.cur_price:.0f}/{new_threshold:.0f})")
# endregion

# region Generate slack info
stats_1_hour = TimeIntervalData(prices, EMA_NUM_HOURS, 1)
stats_24_hour = TimeIntervalData(prices, EMA_NUM_HOURS, 24)
stats_7_day = TimeIntervalData(prices, EMA_NUM_HOURS, 24 * 7)

sign_str = "up" if stats.diff_positive else "down"
attachment_pretext = f"{Currency.PRIMARY_CURRENCY_LONG}'s price has gone {sign_str}. Current price: {Currency.SECONDARY_CURRENCY_SYMBOL}{stats.cur_price:,.0f}"
image_url = PRICE_UP_IMAGE if stats.diff_positive else PRICE_DOWN_IMAGE

# noinspection PyListCreation
attachments = []
attachments.append(format_stat(stats_1_hour, "Price 1 hour ago:      ", attachment_pretext))
attachments.append(format_stat(stats_24_hour, "Price 24 hours ago:  "))
attachments.append(format_stat(stats_7_day, "Price 7 days ago:      "))
# endregion

print("Posting to slack")
Slack.post_to_slack(BOT_NAME, image_url, "", attachments, SLACK_URL, SLACK_CHANNEL)

history.save()

print("Done")

