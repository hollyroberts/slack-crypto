import requests
from datetime import datetime, timedelta
from stats import Stats
from coinbase import Coinbase

# Configurable Constants
PRIMARY_CURRENCY = "BTC"
SECONDARY_CURRENCY = "USD"
EMA_NUM_HOURS = 12

# 'Hard' Constants
API_URL = "https://api.pro.coinbase.com"
CURRENCY_PAIR = f"{PRIMARY_CURRENCY}-{SECONDARY_CURRENCY}"

# Time param info
time_now = datetime.now()
time_start = time_now - timedelta(hours=12)
params = {
    "start": time_start.isoformat(),
    "end": time_now.isoformat(),
    "granularity": 3600
}

# Get data and convert accordingly
historical_data = requests.get(f"{API_URL}/products/{CURRENCY_PAIR}/candles", params=params).text
cb = Coinbase(historical_data)
prices = cb.price_list()
ema = Stats.ema(prices[::-1], EMA_NUM_HOURS)

print(f"{EMA_NUM_HOURS} Hour EMA: {ema}")
print(f"Current price: {cb.latest_price()}")
