from datetime import datetime, timedelta
import json
from enum import Enum

import requests

class Intervals(Enum):
    HOUR = 60
    MINUTE_15 = 15
    MINUTE_5 = 5

class Coinbase:
    API_URL = "https://api.pro.coinbase.com"
    CANDLES_TO_RETRIEVE = 300
    interval = Intervals.MINUTE_15.value

    def __init__(self):
        historical_data = self.__retrieve_from_coinbase()

        # Parse https://docs.pro.coinbase.com/#get-historic-rates
        self.data = []
        for entry in historical_data[::round(Intervals.HOUR.value / self.interval)]:
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
            # print(datetime.fromtimestamp(self.data[i]['time']).strftime("%d/%m/%Y - %H:%M"))
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

    """Retrieve the un filtered results from coinbase according to the interval"""
    def __retrieve_from_coinbase(self):
        # Time param info for request
        time_delta = timedelta(minutes=self.CANDLES_TO_RETRIEVE * self.interval)
        time_now = datetime.utcnow()
        time_start = time_now - time_delta

        params = {
            "granularity": 60 * self.interval
        }
        historical_data = []

        # Send request
        print(f"Retrieving data from coinbase (Interval: {self.interval}m)")
        for i in range(round(Intervals.HOUR.value / self.interval)):
            params["start"] = time_start.isoformat()
            params["end"] = time_now.isoformat()

            json_text = requests.get(f"{self.API_URL}/products/{Currency.CURRENCY_PAIR}/candles", params=params).text
            historical_data += json.loads(json_text)

            time_now -= time_delta
            time_start -= time_delta

            # Ugly hack
            if i == 0:
                time_now -= timedelta(minutes=self.interval)

        return historical_data

class Currency:
    PRIMARY_CURRENCY = "BTC"
    PRIMARY_CURRENCY_LONG = "Bitcoin"
    SECONDARY_CURRENCY = "USD"
    SECONDARY_CURRENCY_SYMBOL = "$"

    CURRENCY_PAIR = f"{PRIMARY_CURRENCY}-{SECONDARY_CURRENCY}"
