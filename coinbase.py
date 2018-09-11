import time
from datetime import datetime, timedelta
import json

import requests

class Currencies:
    CRYPTO_DEFAULT = "BTC"
    FIAT_DEFAULT = "USD"

    CRYPTO_MAP = {
        "BTC": ["Bitcoin"],
        "BCH": ["Bitcoin Cash", "BCash"],
        "ETH": ["Ethereum"],
        "ETC": ["Ethereum Classic"],
        "LTC": ["Litecoin"]
    }

    FIAT_MAP = {
        "EUR": ["Euro", "Euros"],
        "GBP": ["Pound", "Pounds", "Sterling", "Great British Pounds"],
        "USD": ["Dollar", "Dollars", "Freedom Money", "Buck", "Bucks"]
    }

    FIAT_SYMBOL_MAP = {
        "EUR": "€",
        "GBP": "£",
        "USD": "$"
    }

    @classmethod
    def default(cls):
        return Currency(cls.CRYPTO_DEFAULT, cls.FIAT_DEFAULT)

    """Used to improve access to maps"""
    @staticmethod
    def get_map_match(curr_map: dict, string: str):
        string_lower = string.lower()

        for key in curr_map:
            if string_lower == key.lower():
                return key

            value_list = curr_map[key]
            for value in value_list:
                if string_lower == value.lower():
                    return key

        return None

class Currency:
    def __init__(self, primary: str, secondary: str):
        self.primary = primary
        self.primary_long = Currencies.CRYPTO_MAP[primary][0]

        self.secondary = secondary
        self.secondary_symbol = Currencies.FIAT_SYMBOL_MAP[secondary]

        self.pair = f"{primary}-{secondary}"

class Coinbase:
    API_URL = "https://api.pro.coinbase.com"
    CANDLES_TO_RETRIEVE = 300
    MINS_IN_HOUR = 60
    SECS_IN_MINUTE = 60

    def __init__(self, currency: Currency, interval: int = 60):
        self.currency = currency
        self.interval = interval

    """Retrieves last 300 hourly prices (according to interval)"""
    def price_list(self):
        historical_data = self.__retrieve_from_coinbase()

        # Parse https://docs.pro.coinbase.com/#get-historic-rates
        data = []
        for entry in historical_data[::round(self.MINS_IN_HOUR / self.interval)]:
            data.append({
                "time": entry[0],
                "low": entry[1],
                "high": entry[2],
                "open": entry[3],
                "close": entry[4],
                "volume": entry[5]
            })

        # Ensure timestamps are every hour
        for i in range(len(data) - 1):
            # print(datetime.fromtimestamp(self.data[i]['time']).strftime("%d/%m/%Y - %H:%M"))
            time_diff = data[i]['time'] - data[i + 1]['time']
            # print(time_diff)
            assert time_diff == self.SECS_IN_MINUTE * self.MINS_IN_HOUR

        """ Print information
        for entry in self.data:
            time_formatted = datetime.fromtimestamp(entry['time']).strftime("[%d/%m/%Y] %H:%M:%S")
            print(time_formatted + " - " + str(entry['open']))
        """

        prices = []
        for entry in data:
            prices.append(entry['open'])

        return prices

    """Query the API for a specific price"""
    def price_days_ago(self, days: int):
        time_ago = datetime.utcnow() - timedelta(days=days)

        historical_data = self.get_historical_prices(time_ago - timedelta(minutes=1), time_ago)
        historical_time = historical_data[0][0]
        historical_price = historical_data[0][3]

        print(f"Price {days} days ago was {self.currency.secondary_symbol}{historical_price} (exact time: " + datetime.fromtimestamp(historical_time).strftime("%d/%m/%Y - %H:%M") + ")")
        return historical_price

    """Retrieve the un filtered results from coinbase according to the interval"""
    def __retrieve_from_coinbase(self):
        # Time param info for request
        time_delta = timedelta(minutes=self.CANDLES_TO_RETRIEVE * self.interval)
        time_end = datetime.utcnow()
        time_start = time_end - time_delta

        historical_data = []

        # Send request
        print(f"Retrieving data from coinbase (interval {self.interval} mins)")
        for i in range(round(self.MINS_IN_HOUR / self.interval)):
            historical_data += self.get_historical_prices(time_start, time_end)

            time_end -= time_delta
            time_start -= time_delta

            # Ugly hack
            if i == 0:
                time_end -= timedelta(minutes=self.interval)

        return historical_data

    """Get prices closest to the times given, but they cannot be later"""
    def get_prices_closest_to_time(self, *args: datetime):
        earliest = min(args)
        latest = max(args)

        # Map response to ordered list of time -> price
        response = self.get_historical_prices(earliest, latest)
        time_prices = ((datetime.utcfromtimestamp(entry[0]), entry[3]) for entry in response)
        time_prices = sorted(time_prices, key=lambda x: x[0])

        prices = []
        for required_time in args:
            closest_floor = max(entry for entry in time_prices if entry[0] < required_time)
            prices.append(closest_floor[1])

        return tuple(prices)

    """Get historical prices from coinbase unaltered
    Date objects must be UTC"""
    def get_historical_prices(self, start: datetime, end: datetime):
        params = {
            "start": start.isoformat(),
            "end": end.isoformat(),
            "granularity": self.interval * self.SECS_IN_MINUTE
        }

        json_text = self.__get_request(f"{self.API_URL}/products/{self.currency.pair}/candles", params=params)
        return json.loads(json_text)

    @staticmethod
    def __get_request(url: str, params: dict):
        while True:
            resp = requests.get(url, params=params)

            if resp.status_code == 429:
                print("GET request received 429 (timeout). Waiting 1 second and trying again")
                time.sleep(1)
                continue
            elif resp.status_code != 200:
                print("API error - Response code was not 200 or 429")
                raise IOError("Code not 200")
            else:
                return resp.text
