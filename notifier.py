import requests
from datetime import datetime, timedelta
from stats import Stats
from coinbase import Coinbase

# Configurable Constants
PRIMARY_CURRENCY = "BTC"
SECONDARY_CURRENCY = "USD"
EMA_THRESHOLD_PERCENT = 2.5
EMA_NUM_HOURS = 12
HOURS_BETWEEN_POSTS = 6

# 'Hard' Constants
API_URL = "https://api.pro.coinbase.com"
CURRENCY_PAIR = f"{PRIMARY_CURRENCY}-{SECONDARY_CURRENCY}"

# region Functions
def outside_threshold(price_data: list, offset: int):
    if offset > 0:
        price_data = price_data[offset:]

    cur_price = price_data[0]
    ema = Stats.ema(price_data[::-1], EMA_NUM_HOURS)

    diff = abs(cur_price - ema)
    percent_diff = diff / ema
    percent_diff *= 100
    return percent_diff > EMA_THRESHOLD_PERCENT
# endregion

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
prices = cb.price_list()

for i in range(24):
    outside_threshold(prices, i)
