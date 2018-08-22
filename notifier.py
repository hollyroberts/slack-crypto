import requests
import json
from datetime import datetime, timedelta

# Constants
API_URL = "https://api.pro.coinbase.com"

PRIMARY_CURRENCY = "BTC"
SECONDARY_CURRENCY = "USD"
CURRENCY_PAIR = f"{PRIMARY_CURRENCY}-{SECONDARY_CURRENCY}"

# Time param info
time_now = datetime.now()
time_start = time_now - timedelta(hours=12)
params = {
    "start": time_start.isoformat(),
    "end": time_now.isoformat(),
    "granularity": 3600
}

historical_price = requests.get(f"{API_URL}/products/{CURRENCY_PAIR}/candles", params=params).text
historical_price = json.loads(historical_price)

for entry in historical_price:
    # https://docs.pro.coinbase.com/#get-historic-rates
    time = entry[0]
    open_price = entry[3]

    time_formatted = datetime.fromtimestamp(time).strftime("[%d/%m/%Y] %H:%M:%S")
    print(time_formatted + " - " + str(open_price))
