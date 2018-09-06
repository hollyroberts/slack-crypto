import requests
import json

from coinbase import Currency
from stats import HourData
from misc import Misc

class Slack:
    @classmethod
    def post_to_slack(cls, name: str, icon_url: str, text: str, attachments: list, slack_url: str, channel=""):
        slack_data = {"username": name, "icon_url": icon_url, "text": text, "attachments": attachments, "channel": channel}
        response = "null"

        try:
            response = requests.post(slack_url, data=json.dumps(slack_data), headers={"content-type": "application/json"})
            if response.status_code != requests.codes.ok:
                cls.slack_error_msg(response, slack_data)
                return -1
        except requests.exceptions.ConnectionError:
            print("Connection refused")
            cls.slack_error_msg(response, slack_data)
            return -1
        except Exception as e:
            print("An exception occurred:")
            print(e)
            cls.slack_error_msg(response, slack_data)
            return -1

    @classmethod
    def slack_error_msg(cls, response, slack_data):
        print("An error occurred posting to slack")
        print("Response given:")
        print(response)
        print("Data sent:")
        print(slack_data)

    @classmethod
    def generate_attachment(cls, prices: list, stats: HourData, ema: int):
        stats_1_hour = HourData(prices, ema, 1)
        stats_24_hour = HourData(prices, ema, 24)
        stats_7_day = HourData(prices, ema, 24 * 7)

        sign_str = "up" if stats.is_diff_positive else "down"
        attachment_pretext = f"{Currency.PRIMARY_CURRENCY_LONG}'s price has gone {sign_str}. Current price: {Currency.SECONDARY_CURRENCY_SYMBOL}{stats.cur_price:,.0f}"

        # noinspection PyListCreation
        attachments = []
        attachments.append(Misc.format_stat(stats_1_hour, stats, "Price 1 hour ago:      ", attachment_pretext))
        attachments.append(Misc.format_stat(stats_24_hour, stats, "Price 24 hours ago:  "))
        attachments.append(Misc.format_stat(stats_7_day, stats, "Price 7 days ago:      "))
        
        return attachments
