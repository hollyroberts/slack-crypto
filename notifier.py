import requests
from datetime import datetime, timedelta
from stats import Stats
from coinbase import Coinbase

# Configurable Constants
PRIMARY_CURRENCY = "BTC"
SECONDARY_CURRENCY = "USD"
NUM_HOURS = 12


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

# Get data and format into data structure
historical_data = requests.get(f"{API_URL}/products/{CURRENCY_PAIR}/candles", params=params).text
cb = Coinbase(historical_data)
cb.print_historical_prices()
