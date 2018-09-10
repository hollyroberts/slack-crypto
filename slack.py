import requests
import json

from coinbase import Currency, Coinbase
from stats import HourData
from constants import SlackColourThresholds

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
    def generate_attachment(cls, prices: list, current_stats: HourData, ema: int):
        stats_1_hour = HourData(prices, ema, 1)
        stats_24_hour = HourData(prices, ema, 24)
        stats_7_day = HourData(prices, ema, 24 * 7)

        sign_str = "up" if current_stats.is_diff_positive else "down"
        attachment_pretext = f"{Currency.PRIMARY_CURRENCY_LONG}'s price has gone {sign_str}. Current price: {Currency.SECONDARY_CURRENCY_SYMBOL}{current_stats.cur_price:,.0f}"

        # noinspection PyListCreation
        attachments = []
        attachments.append(cls.format_stat_wrapper(stats_1_hour, current_stats, "Price 1 hour ago:      ", attachment_pretext))
        attachments.append(cls.format_stat_wrapper(stats_24_hour, current_stats, "Price 24 hours ago:  "))
        attachments.append(cls.format_stat_wrapper(stats_7_day, current_stats, "Price 7 days ago:      "))

        # Try to add 28 day stats
        # noinspection PyBroadException
        try:
            price_28_days = Coinbase.price_days_ago(28)
            attachments.append(cls.format_stat(price_28_days, current_stats.cur_price, "Price 28 days ago:     "))
        except Exception as e:
            print(e)
            print("Ignoring error, posting 3 historical prices instead of 4 (28 day price omitted)")
        
        return attachments

    @classmethod
    def format_stat_wrapper(cls, stat: HourData, stats: HourData, text_pretext: str, pretext=None):
        return cls.format_stat(stat.cur_price, stats.cur_price, text_pretext, pretext)

    @staticmethod
    def format_stat(historical_price, cur_price, text_pretext: str, pretext=None):
        diff = cur_price - historical_price
        diff /= historical_price
        diff *= 100

        if diff > SlackColourThresholds.GOOD:
            colour = "good"
        elif diff > SlackColourThresholds.NEUTRAL:
            colour = ""
        elif diff > SlackColourThresholds.WARNING:
            colour = "warning"
        else:
            colour = "danger"

        text = f"{text_pretext}{Currency.SECONDARY_CURRENCY_SYMBOL}{historical_price:,.0f} ({diff:+.2f}%)"
        attachment = {"fallback": "some price changes", "text": text, "color": colour}
        if pretext is not None:
            attachment['pretext'] = pretext

        return attachment
