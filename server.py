import hashlib
from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse as urlparse
import hmac
import time
from coinbase import Coinbase, Currencies, Currency
import shlex
from slack import Slack
from datetime import datetime, timedelta
import requests
import json
import threading

class CommandHandler(BaseHTTPRequestHandler):
    # Seconds to allow for timestamp mismatch
    # SHA-256 should be secure enough to set it to 5 minutes (value given in docs)
    REPLAY_PREVENTION = 300

    # Maximum days to be allowed to retrieve
    MAX_DAYS = 20

    VERSION = "v0"
    SIGNING_SECRET = ""

    SIG_STRING = "X-Slack-Signature"
    REQ_TS = "X-Slack-Request-Timestamp"
    CONTENT_TYPE = "application/x-www-form-urlencoded"

    # Required headers. None means that the value doesn't matter
    REQUIRED_HEADERS = {
        "Content-Type": CONTENT_TYPE,
        SIG_STRING: None,
        REQ_TS: None
    }

    # POST is for submitting data.
    # noinspection PyPep8Naming
    def do_POST(self):
        print(f"Incoming HTTP POST: {self.path}")

        if not self.basic_header_verification():
            self.send_error(400)
            return

        # Get and parse body data
        content_length = int(self.headers.get('Content-Length', 0))
        body_data = self.rfile.read(content_length).decode("utf-8")
        body_dict = urlparse.parse_qs(body_data)

        if not self.verify_signature(body_data):
            self.send_error(401)
            return

        # Parse args
        try:
            currency, days = self.parse_args(body_dict)
        except ParseError as e:
            print(f"Parse error: {e}")
            self.initial_response(f"Parse error: {e}")
            return

        # Don't allow more than 20 days to be retrieved
        if len(days) > self.MAX_DAYS:
            print(f"Number of days was greater than {self.MAX_DAYS}")
            self.initial_response(f"Max number of days to request is {self.MAX_DAYS}")
            return

        # Send 200
        print("Sending initial 200 response")
        if len(days) > 2:
            self.initial_response(f"Retrieving data for {len(days)} days, this may take a few seconds")
        else:
            self.initial_response()

        # Process request on separate thread to not block 200 response
        t = threading.Thread(target=self.post_200_code, args=(currency, days, body_dict['response_url'][0]))
        t.daemon = True
        t.start()

    def post_200_code(self, currency, days, url):
        # Get prices and attachment from prices
        try:
            slack_attachments = self.create_slack_attachments(currency, days)
        except IOError as e:
            print(e)
            self.send_response_msg(url, {"text": "Error retrieving data, please try again later (or complain at blackened)"})
            return

        # Post to slack
        print("Posting to slack")
        self.send_response_msg(url, {"attachments": slack_attachments}, ephemeral=False)

    @staticmethod
    def create_slack_attachments(currency: Currency, days: list):
        cb = Coinbase(currency, 1)
        time_now = datetime.utcnow()

        # Get 0/1/24 hour prices
        minute_prices = cb.get_historical_prices(time_now - timedelta(minutes=60), time_now)
        print(minute_prices)
        cur_price = minute_prices[0][3]
        price_1_hour = minute_prices[60][3]
        price_24_hour = cb.price_days_ago(1)

        # Get day prices
        day_prices = {}
        for day in days:
            day_prices[day] = cb.price_days_ago(day)

        # Create message
        pretext = f"{currency.primary_long}'s current price is: {currency.secondary_symbol}{Slack.format_num(cur_price)}"
        attachments = Slack.generate_attachments(currency, {1: price_1_hour, 24: price_24_hour}, cur_price, True)
        attachments += Slack.generate_attachments(currency, day_prices, cur_price, False)
        attachments[0]['pretext'] = pretext

        return attachments

    def parse_args(self, body_dict: dict):
        # Default values
        print("Parsing args")
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
            currency = self.parse_currency_args_1(messages[0])
        elif num_str_args == 2:
            currency = self.parse_currency_args_2(messages)
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

    """Checks that message was from slack and has headers we expect"""
    def basic_header_verification(self):
        for header in self.REQUIRED_HEADERS:
            # Header exists
            if header not in self.headers:
                print(f"Did not receive header {header}")
                return False

            # Header has value expected
            req_val = self.REQUIRED_HEADERS[header]
            if req_val is None:
                continue

            if self.headers[header] != req_val:
                print(f"Header {header} was not \"{req_val}\", instead was \"{self.headers[header]}\"")
                return False

        return True

    """Verify that message was given by slack
    https://api.slack.com/docs/verifying-requests-from-slack"""
    def verify_signature(self, body: str):
        print("Verifying signature")

        # Read headers
        given_sig = self.headers[self.SIG_STRING]
        timestamp = self.headers[self.REQ_TS]

        # Ensure timestamp isn't too old
        unix_now = time.time()
        time_diff = unix_now - int(timestamp)
        if time_diff > self.REPLAY_PREVENTION:
            print(f"Time difference was too large ({time_diff:,.0f} seconds)")
            return False

        # Compute signature
        sig_basestring = self.VERSION + ":" + timestamp + ":" + body
        digest = hmac.new(str.encode(self.SIGNING_SECRET), sig_basestring.encode("utf-8"), digestmod=hashlib.sha256)
        computed_sig = self.VERSION + "=" + digest.hexdigest()

        # Compare
        if hmac.compare_digest(computed_sig, given_sig):
            return True
        else:
            print("Signatures don't match")
            print(f"Given: {given_sig}")
            print(f"Expected: {computed_sig}")

    @staticmethod
    def send_response_msg(url, json_msg, ephemeral=True):
        if ephemeral:
            json_msg['response_type'] = "ephemeral"
        else:
            json_msg['response_type'] = "in_channel"

        requests.post(url, data=json.dumps(json_msg), headers={"content-type": "application/json"})

    """Send 200 message back"""
    def initial_response(self, message: str = None):
        self.send_response(200)
        self.end_headers()

        if message is not None:
            self.wfile.write(message.encode())

    """Debug method to print body contents received"""
    @staticmethod
    def print_body_dict(body_dict: dict):
        for key in body_dict:
            print(key + ": " + body_dict[key][0])

    @staticmethod
    def run(port):
        server = HTTPServer(('', port), CommandHandler)
        print(f"Web server started on port {port}")
        server.serve_forever()

class ParseError(Exception):
    pass
