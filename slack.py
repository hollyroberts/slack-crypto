import requests
import json

from coinbase import Currencies, Currency, Coinbase
from stats import HourData
from constants import SlackColourThresholds

class Slack:
    ATTACHMENT_MIN_WIDTH = 23

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
    def generate_attachments(cls, currency: Currency, hour_price_map: dict, cur_price: float, hours):
        attachments = []

        for time_ago in sorted(hour_price_map.keys()):
            price_ago = hour_price_map[time_ago]

            attachments.append(cls.format_stat_new(cur_price, price_ago, currency, time_ago, hours))

        return attachments

    @classmethod
    def generate_post(cls, prices: list, current_stats: HourData):
        cur_price = current_stats.cur_price
        price_1_hour = prices[1]
        price_24_hour = prices[24]
        price_7_day = prices[24 * 7]

        currency = Currency(Currencies.PRIMARY_CURRENCY, Currencies.SECONDARY_CURRENCY)

        sign_str = "up" if current_stats.is_diff_positive else "down"
        attachment_pretext = f"{Currencies.PRIMARY_CURRENCY_LONG}'s price has gone {sign_str}. Current price: {Currencies.SECONDARY_CURRENCY_SYMBOL}{current_stats.cur_price:,.0f}"

        # noinspection PyListCreation
        attachments = []

        hour_entry = cls.format_stat_new(cur_price, price_1_hour, currency, 1)
        hour_entry['pretext'] = attachment_pretext
        attachments.append(hour_entry)
        attachments.append(cls.format_stat_new(cur_price, price_24_hour, currency, 24))
        attachments.append(cls.format_stat_new(cur_price, price_7_day, currency, 7, False))

        # Try to add 28 day stats
        # noinspection PyBroadException
        try:
            price_28_days = Coinbase.price_days_ago(28)
            attachments.append(cls.format_stat_new(cur_price, price_28_days, currency, False))
        except Exception as e:
            print(e)
            print("Ignoring error, posting 3 historical prices instead of 4 (28 day price omitted)")
        
        return attachments

    @classmethod
    def format_stat_new(cls, cur_price: float, historical_price: float, currency: Currency, units_ago: int, hours=True):
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

        time_unit = "hour" if hours else "day"
        if units_ago != 1:
            time_unit += "s"
        pretext = f"Price {units_ago} {time_unit} ago:"

        text = f"{pretext:<{cls.ATTACHMENT_MIN_WIDTH}}{currency.secondary_symbol}{historical_price:,.0f} ({diff:+.2f}%)"
        attachment = {"fallback": "some price changes", "text": text, "color": colour}

        return attachment
