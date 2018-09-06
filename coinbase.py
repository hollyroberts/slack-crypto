from datetime import datetime, timedelta
import json
import requests

class Coinbase:
    API_URL = "https://api.pro.coinbase.com"
    CANDLES_TO_RETRIEVE = 300

    def __init__(self):
        # Time param info for request
        time_now = datetime.utcnow()
        time_start = time_now - timedelta(hours=self.CANDLES_TO_RETRIEVE)  # CB should give 300 results, lets make sure of it
        params = {
            "start": time_start.isoformat(),
            "end": time_now.isoformat(),
            "granularity": 3600
        }

        # Send request
        json_text = requests.get(f"{self.API_URL}/products/{Currency.CURRENCY_PAIR}/candles", params=params).text
        historical_data = json.loads(json_text)

        # Parse https://docs.pro.coinbase.com/#get-historic-rates
        self.data = []
        for entry in historical_data:
            self.data.append({
                "time": entry[0],
                "low": entry[1],
                "high": entry[2],
                "open": entry[3],
                "close": entry[4],
                "volume": entry[5]
            })

        # Ensure timestamps are every hour
        for i in range(len(self.data) - 1):
            time_diff = self.data[i]['time'] - self.data[i + 1]['time']
            assert time_diff == 3600

    def latest_price(self):
        return self.data[0]['open']

    """Return a list of the last prices in reverse order (using open)"""
    def price_list(self):
        prices = []
        for entry in self.data:
            prices.append(entry['open'])

        return prices

    """Debug method to print datetime and price"""
    def print_historical_prices(self):
        for entry in self.data:
            time_formatted = datetime.fromtimestamp(entry['time']).strftime("[%d/%m/%Y] %H:%M:%S")
            print(time_formatted + " - " + str(entry['open']))

class Currency:
    PRIMARY_CURRENCY = "BTC"
    PRIMARY_CURRENCY_LONG = "Bitcoin"
    SECONDARY_CURRENCY = "USD"
    SECONDARY_CURRENCY_SYMBOL = "$"

    CURRENCY_PAIR = f"{PRIMARY_CURRENCY}-{SECONDARY_CURRENCY}"
