from datetime import datetime
import json

class Coinbase():
    def __init__(self, json_text: str):
        historical_data = json.loads(json_text)

        self.data = []
        for entry in historical_data:
            self.data.append({
                # https://docs.pro.coinbase.com/#get-historic-rates
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
