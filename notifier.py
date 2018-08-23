import requests
import sys

from datetime import datetime, timedelta
from stats import TimeIntervalData
from coinbase import Coinbase
from slack import Slack

# Configurable Constants
PRIMARY_CURRENCY = "BTC"
PRIMARY_CURRENCY_LONG = "Bitcoin"
SECONDARY_CURRENCY = "USD"
SECONDARY_CURRENCY_SYMBOL = "$"
EMA_THRESHOLD_PERCENT = 4
EMA_NUM_HOURS = 18
HOURS_BETWEEN_POSTS = 6

COLOUR_THRESHOLD_GOOD = 1.5
COLOUR_THRESHOLD_NEUTRAL = -1
COLOUR_THRESHOLD_WARNING = -3

PRICE_UP_IMAGE = "https://i.imgur.com/2PVZ0l1.png"
PRICE_DOWN_IMAGE = "https://i.imgur.com/21sDn3D.png"
BOT_NAME = "Cryptocorn"
SLACK_CHANNEL = "#crypto"

# 'Hard' Constants
API_URL = "https://api.pro.coinbase.com"
CURRENCY_PAIR = f"{PRIMARY_CURRENCY}-{SECONDARY_CURRENCY}"
SLACK_URL = sys.argv[1]

# Time param info
time_now = datetime.now()
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

stats = TimeIntervalData(prices, EMA_NUM_HOURS)
if stats.ema_percent_diff_positive < EMA_THRESHOLD_PERCENT:
    print(f"Current price not outside threshold ({stats.formatted_info()})")
    sys.exit(1)
else:
    print(f"Current price increased above threshold difference ({stats.formatted_info()})")

# Check the last X hours
last_msg_price = None

for offset in range(1, HOURS_BETWEEN_POSTS + 1):
    offset_data = TimeIntervalData(prices, EMA_NUM_HOURS, offset)

    if offset_data.ema_percent_diff_positive < EMA_THRESHOLD_PERCENT:
        continue

    print(f"Data from {offset} hours ago is also above the threshold difference {offset_data.formatted_info()})")

    # If magnitude is opposite then include anyway
    if offset_data.diff_positive != stats.diff_positive:
        print(f"Last increase was the opposite sign ({stats.diff:+.0f}/{offset_data.diff:+.0f})")
        break

    # Allow if increase is greater again
    if offset_data.diff_positive:
        required_perc_diff = (1 + EMA_THRESHOLD_PERCENT / 100)
        sign_str = "above"
    else:
        required_perc_diff = (1 - EMA_THRESHOLD_PERCENT / 100)
        sign_str = "below"

    new_threshold = offset_data.cur_price * required_perc_diff
    print(f"To repost within the cooldown period the current price must be {sign_str}: {new_threshold:.0f}")
    if (offset_data.diff_positive and stats.cur_price > new_threshold) or \
            (not offset_data.diff_positive and stats.cur_price < new_threshold):
        print(f"Beats new threshold price ({stats.cur_price:.0f}/{new_threshold:.0f})")
        break

    print(f"Does not beat new threshold price: ({stats.cur_price:.0f}/{new_threshold:.0f})")
    sys.exit(1)

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
