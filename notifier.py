import requests
import sys
import argparse
import json
from pathlib import Path

from datetime import datetime, timedelta
from stats import TimeIntervalData
from coinbase import Coinbase
from slack import Slack

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
args = parser.parse_args()
# endregion
# region Constants

# Configurable Constants
PRIMARY_CURRENCY = "BTC"
PRIMARY_CURRENCY_LONG = "Bitcoin"
SECONDARY_CURRENCY = "USD"
SECONDARY_CURRENCY_SYMBOL = "$"
EMA_THRESHOLD_PERCENT = args.threshold
EMA_NUM_HOURS = args.ema
HOURS_BETWEEN_POSTS = args.cooldown

COLOUR_THRESHOLD_GOOD = 1.5
COLOUR_THRESHOLD_NEUTRAL = -1
COLOUR_THRESHOLD_WARNING = -3

PRICE_UP_IMAGE = "https://i.imgur.com/2PVZ0l1.png"
PRICE_DOWN_IMAGE = "https://i.imgur.com/21sDn3D.png"
BOT_NAME = args.name
SLACK_CHANNEL = args.channel

# 'Hard' Constants
# https://docs.pro.coinbase.com/#get-historic-rates
API_URL = "https://api.pro.coinbase.com"
CURRENCY_PAIR = f"{PRIMARY_CURRENCY}-{SECONDARY_CURRENCY}"
SLACK_URL = args.url
SCRIPT_NAME = Path(__file__).stem
DATA_FILE = Path(f"last_post_data_{SCRIPT_NAME}.json")

# endregion

# Time param info
time_now = datetime.utcnow()
time_start = time_now - timedelta(hours=12)  # Doesn't matter because CB will return 300 results
params = {
    "start": time_start.isoformat(),
    "end": time_now.isoformat(),
    "granularity": 3600
}

# Get data and convert accordingly
historical_data = requests.get(f"{API_URL}/products/{CURRENCY_PAIR}/candles", params=params).text
cb = Coinbase(historical_data)
cur_price = cb.latest_price()
prices = cb.price_list()

# Check whether to update
stats = TimeIntervalData(prices, EMA_NUM_HOURS)
if stats.ema_percent_diff_positive < EMA_THRESHOLD_PERCENT:
    print(f"Current price not outside threshold ({stats.formatted_info()})")
    sys.exit(1)
else:
    print(f"Current price increased above threshold difference ({stats.formatted_info()})")

# region Last post checks
""" 
Check whether last post stops from posting
Returns true if it does
"""
def last_post_stops_posting():
    print("Checking last post data")
    try:
        with open(DATA_FILE, "r") as f:
            # Read file
            last_data = json.loads(f.read())

            last_price = last_data['price']
            last_time = datetime.strptime(last_data['time_hours'], "%d/%m/%Y - %H")
            last_rising = last_data['rising']
            rising_str = "rising" if last_rising else "falling"

            # Get time difference
            cur_time = datetime.utcnow()
            cur_time = cur_time.replace(minute=0, second=0, microsecond=0)
            hours_diff = cur_time - last_time
            assert hours_diff.seconds % 3600 == 0
            hours_diff = hours_diff.seconds // 3600

            print(f"Last post was {hours_diff} hours ago at a price of {SECONDARY_CURRENCY_SYMBOL}{last_price} ({rising_str})")

            # Perform algorithmic checks
            if hours_diff >= HOURS_BETWEEN_POSTS:
                print(f"Last post was longer ago than the cooldown value ({HOURS_BETWEEN_POSTS})")
                return False

            # If magnitude is opposite then include anyway
            if last_rising != stats.diff_positive:
                print(f"Last change was in the opposite direction")
                return False

            # Allow if increase is greater again
            if last_rising:
                required_perc_diff = (1 + EMA_THRESHOLD_PERCENT / 100)
                threshold_sign_str = "above"
            else:
                required_perc_diff = (1 - EMA_THRESHOLD_PERCENT / 100)
                threshold_sign_str = "below"

            new_threshold = last_price * required_perc_diff
            print(f"To repost within the cooldown period the current price must be {threshold_sign_str}: {new_threshold:.0f}")
            if (last_rising and stats.cur_price > new_threshold) or \
                    (not last_rising and stats.cur_price < new_threshold):
                print(f"Beats new threshold price ({stats.cur_price:.0f}/{new_threshold:.0f})")
                return False

            print(f"Does not beat new threshold price: ({stats.cur_price:.0f}/{new_threshold:.0f})")
            return True
    except Exception as e:
        print(e)
        print("Checks to see whether the last post stops this script from posting failed. Therefore check omitted")
        return False

if last_post_stops_posting():
    sys.exit(1)
# endregion

# Generate slack info
stats_1_hour = TimeIntervalData(prices, EMA_NUM_HOURS, 1)
stats_24_hour = TimeIntervalData(prices, EMA_NUM_HOURS, 24)
stats_7_day = TimeIntervalData(prices, EMA_NUM_HOURS, 24 * 7)

def format_stat(stat: TimeIntervalData, text_pretext: str, pretext=None):
    diff = stats.cur_price - stat.cur_price
    diff /= stat.cur_price
    diff *= 100

    if diff > COLOUR_THRESHOLD_GOOD:
        colour = "good"
    elif diff > COLOUR_THRESHOLD_NEUTRAL:
        colour = ""
    elif diff > COLOUR_THRESHOLD_WARNING:
        colour = "warning"
    else:
        colour = "danger"

    text = f"{text_pretext}{SECONDARY_CURRENCY_SYMBOL}{stat.cur_price:,.0f} ({diff:+.2f}%)"
    attachment = {"fallback": "some price changes", "text": text, "color": colour}
    if pretext is not None:
        attachment['pretext'] = pretext

    return attachment

sign_str = "up" if stats.diff_positive else "down"
attachment_pretext = f"{PRIMARY_CURRENCY_LONG}'s price has gone {sign_str}. Current price: {SECONDARY_CURRENCY_SYMBOL}{stats.cur_price:,.0f}"

# noinspection PyListCreation
attachments = []
attachments.append(format_stat(stats_1_hour, "Price 1 hour ago:      ", attachment_pretext))
attachments.append(format_stat(stats_24_hour, "Price 24 hours ago:  "))
attachments.append(format_stat(stats_7_day, "Price 7 days ago:      "))

image_url = PRICE_UP_IMAGE if stats.diff_positive else PRICE_DOWN_IMAGE
print("Posting to slack")
Slack.post_to_slack(BOT_NAME, image_url, "", attachments, SLACK_URL, SLACK_CHANNEL)
print("Done")
