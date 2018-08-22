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

    def print_historical_prices(self):
        for entry in self.data:
            time_formatted = datetime.fromtimestamp(entry['time']).strftime("[%d/%m/%Y] %H:%M:%S")
            print(time_formatted + " - " + str(entry['open']))
