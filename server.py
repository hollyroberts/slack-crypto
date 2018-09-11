import hashlib
from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse as urlparse
import hmac
import time
from coinbase import Currencies
import shlex
from slack import Slack

class Server(BaseHTTPRequestHandler):
    # Seconds to allow for timestamp mismatch
    # SHA-256 should be secure enough to set it to 5 minutes (value given in docs)
    REPLAY_PREVENTION = 300

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

        # Get body data
        content_length = int(self.headers.get('Content-Length', 0))
        body_data = self.rfile.read(content_length).decode("utf-8")

        # Parse body data
        body_dict = urlparse.parse_qs(body_data)

        if not self.verify_signature(body_data):
            self.send_error(401)
            return

        # Parse args
        try:
            crypto, fiat, days = self.parse_args(body_dict)
        except ParseError as e:
            print(f"Parse error: {e}")
            self.reply(f"Parse error: {e}")
            return
        fiat_symbol = Currency.FIAT_SYMBOL_MAP[fiat]

        # Send 200
        print("Sending initial 200 response")
        self.reply()

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
            currency = Currency(Currencies.PRIMARY_CURRENCY, Currencies.SECONDARY_CURRENCY)

        # Extract, order, remove duplicate days, and remove days < 2
        days = list(int(d) for d in messages[num_str_args:] if int(d) >= 2)
        days = sorted(set(days))

        return currency, days

    @staticmethod
    def parse_currency_args_1(message: str):
        # Is arg crypto?
        crypto = Currencies.get_map_match(Currencies.CRYPTO_MAP, message)
        if crypto is not None:
            return Currency(crypto, Currencies.SECONDARY_CURRENCY)

        # Is arg fiat?
        fiat = Currencies.get_map_match(Currencies.FIAT_MAP, message)
        if fiat is not None:
            return Currency(Currencies.PRIMARY_CURRENCY, fiat)

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

    """Send message back"""
    def reply(self, message: str = None):
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
        server = HTTPServer(('', port), Server)
        print(f"Web server started on port {port}")
        server.serve_forever()

class ParseError(Exception):
    pass
