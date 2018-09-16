import logging
import shlex
from datetime import datetime, timedelta
import requests
import json

from src.coinbase import Currencies, Currency, Coinbase
from src.slack import Slack


class ParseError(Exception):
    pass

"""Static methods for server.py"""
class ServerProcessor:
    @staticmethod
    def send_response_msg(url, json_msg, ephemeral=True):
        if ephemeral:
            json_msg['response_type'] = "ephemeral"
        else:
            json_msg['response_type'] = "in_channel"

        requests.post(url, data=json.dumps(json_msg), headers={"content-type": "application/json"})

    @classmethod
    def parse_args(cls, body_dict: dict):
        # Default values
        logging.info("Parsing args")
        messages = body_dict.get('text', [''])[0]
        messages = shlex.split(messages)

        # Work out which args are what
        num_str_args = 0
        i = 0
        while len(messages) > i:
            msg = messages[i]
            i += 1

            if msg.isdigit():
                break
            num_str_args += 1

        if num_str_args > 2:
            raise ParseError("Received too many non digit entries")

        while len(messages) > i:
            msg = messages[i]
            i += 1

            if not msg.isdigit():
                raise ParseError("Received non digit entry after digit entry")

        # Get currency info
        if num_str_args == 1:
            currency = cls.parse_currency_args_1(messages[0])
        elif num_str_args == 2:
            currency = cls.parse_currency_args_2(messages)
        else:
            currency = Currency(Currencies.CRYPTO_DEFAULT, Currencies.FIAT_DEFAULT)

        # Extract, order, remove duplicate days, and remove days < 2
        days = list(int(d) for d in messages[num_str_args:] if int(d) >= 2)
        if len(days) == 0:
            days = [7, 28]
        days = sorted(set(days))

        return currency, days

    @staticmethod
    def parse_currency_args_1(message: str):
        # Is arg crypto?
        crypto = Currencies.get_map_match(Currencies.CRYPTO_MAP, message)
        if crypto is not None:
            return Currency(crypto, Currencies.FIAT_DEFAULT)

        # Is arg fiat?
        fiat = Currencies.get_map_match(Currencies.FIAT_MAP, message)
        if fiat is not None:
            return Currency(Currencies.CRYPTO_DEFAULT, fiat)

        raise ParseError("Could not parse first argument to cryptocurrency or fiat currency")

    @staticmethod
    def parse_currency_args_2(message: list):
        # Try crypto being first
        crypto = Currencies.get_map_match(Currencies.CRYPTO_MAP, message[0])
        if crypto is not None:
            fiat = Currencies.get_map_match(Currencies.FIAT_MAP, message[1])
            if fiat is None:
                raise ParseError("First argument was a cryptocurrency, but second argument was not a fiat currency")

            return Currency(crypto, fiat)

        # Try fiat being first
        fiat = Currencies.get_map_match(Currencies.FIAT_MAP, message[0])
        if fiat is not None:
            crypto = Currencies.get_map_match(Currencies.CRYPTO_MAP, message[1])
            if crypto is None:
                raise ParseError("First argument was a fiat currency, but second argument was not a cryptocurrency")

            return Currency(crypto, fiat)

    @staticmethod
    def create_slack_attachments(currency: Currency, days: list):
        cb = Coinbase(currency, 1)
        time_now = datetime.utcnow()

        # Get 0/1/24 hour prices
        cur_price, price_1_hour = cb.get_prices_closest_to_time(time_now, time_now - timedelta(minutes=60))
        price_24_hour = cb.price_days_ago(1)

        # Get day prices
        day_prices = {}
        for day in days:
            day_prices[day] = cb.price_days_ago(day)

        # Create message
        pretext = f"{currency.crypto_long}'s current price is: {currency.fiat_symbol}{Slack.format_num(cur_price)}"
        attachments = Slack.generate_attachments(currency, {1: price_1_hour, 24: price_24_hour}, cur_price, True)
        attachments += Slack.generate_attachments(currency, day_prices, cur_price, False)
        attachments[0]['pretext'] = pretext

        return attachments

    """Wrapper for starting threading"""
    @classmethod
    def post_200_code(cls, url, user, currency, days):
        # noinspection PyBroadException
        try:
            cls.__post_200_code(url, user, currency, days)
        except Exception:
            logging.exception("Exception occurred in thread", exc_info=True)

    """Implementation of post_200_code"""
    @staticmethod
    def __post_200_code(url, user, currency, days):
        # Get prices and attachment from prices
        try:
            slack_attachments = ServerProcessor.create_slack_attachments(currency, days)
        except IOError as e:
            logging.exception(e, exc_info=True)
            ServerProcessor.send_response_msg(url, {
                "text": "Error retrieving data, please try again later (or complain at blackened)"})
            return

        # Post to slack
        logging.info("Posting to slack")
        json_msg = {
            "text": f"{user} requested a price report",
            "attachments": slack_attachments
        }
        ServerProcessor.send_response_msg(url, json_msg, ephemeral=False)

    """Debug method to print body contents received"""
    @staticmethod
    def print_body_dict(body_dict: dict):
        for key in body_dict:
            logging.info(key + ": " + body_dict[key][0])