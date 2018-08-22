import requests
from datetime import datetime, timedelta
from stats import TimeIntervalData
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
prices = Coinbase(historical_data).price_list()

stats = TimeIntervalData(prices, EMA_NUM_HOURS)
if stats.ema_percent_diff < EMA_THRESHOLD_PERCENT:
    print(f"Current price not outside threshold ({stats.cur_price:.0f}/{stats.ema:.0f} - {stats.ema_percent_diff:.1f}%)")
