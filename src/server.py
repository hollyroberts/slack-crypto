import logging
import time

from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse as urlparse
import hashlib
import hmac
import threading

from src.coinbase import Currencies
from src.server_processor import ServerProcessor, ParseError

"""Override methods of HTTPServer to improve logging"""
class CustomHTTPServer(HTTPServer):
    def handle_error(self, request, client_address):
        logging.exception(f"Exception happened during processing of request from {client_address}", exc_info=True)

class CommandHandler(BaseHTTPRequestHandler):
    # Seconds to allow for timestamp mismatch
    # SHA-256 should be secure enough to set it to 5 minutes (value given in docs)
    REPLAY_PREVENTION = 300

    # Maximum days to be allowed to retrieve
    MAX_DAYS = 10

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
        logging.info(f"Incoming HTTP POST: {self.path}")

        if self.path != "/slack/crypto":
            logging.info("Path not /slack/crypto")
            self.send_error(400)
            return

        if not self.basic_header_verification():
            self.send_error(400)
            return

        # Get and parse body data
        content_length = int(self.headers.get('Content-Length', 0))
        body_data = self.rfile.read(content_length).decode("utf-8")
        body_dict = urlparse.parse_qs(body_data)

        response_url = body_dict['response_url'][0]
        username = body_dict['user_name'][0]

        # Verify signature
        if not self.verify_signature(body_data):
            self.send_error(401)
            return

        # Log request
        logging.debug("Request info:")
        logging.debug("Username: " + body_dict['user_name'][0])
        logging.debug("Channel: " + body_dict['channel_name'][0] + " (" + body_dict['channel_id'][0] + ")")
        logging.debug("Command: " + body_dict['command'][0] + " " + body_dict.get('text', [''])[0])

        # Process help message instead
        if self.help_message(body_dict):
            return

        # Parse args
        try:
            currency, days = ServerProcessor.parse_args(body_dict)
        except ParseError as e:
            logging.warning(f"Parse error: {e}")
            self.initial_response(f"Parse error: {e}"
                                  f"\nUse `/prices help` for help")
            return

        # Don't allow more than 20 days to be retrieved
        if len(days) > self.MAX_DAYS:
            logging.info(f"Number of days was greater than {self.MAX_DAYS}")
            self.initial_response(f"Max number of days to request is {self.MAX_DAYS}")
            return

        # Send 200
        # Temporary code to notify about GBP support (TODO remove after a month)
        logging.info("Sending initial 200 response")
        resp = []
        if len(days) > 2:
            resp.append(f"Retrieving data for {len(days)} days, this may take a few seconds")
        if currency.fiat == "GBP" and currency.crypto != "BTC":
            resp.append("The GBP currency has only just been added for certain trading pairs, manually reduce the days to retrieve (otherwise this command will fail)")
        self.initial_response('\n'.join(resp))

        # Process request on separate thread to not block 200 response
        logging.debug("Starting the separate thread to handle the rest of the processing")
        t = threading.Thread(target=ServerProcessor.post_200_code, args=(response_url, username, currency, days))
        t.daemon = True
        t.start()

    def help_message(self, body_dict: dict):
        text = body_dict.get("text", [""])[0].lower()
        if not(text == "h" or text == "help"):
            return False

        return_msg = "The first 2 arguments can be optionally used to specify the cryptocurrency and fiat pair (1 or both can be omitted)\n" \
                     "The remaining arguments are the number of days back you want to retrieve prices for (eg. /prices \"bitcoin cash\" 7 14 will retrieve the price 1 and 2 weeks ago for bitcoin cash). " \
                     "By default the price 7 and 28 days ago are fetched" \
                     "\n\nSupported cryptocurrencies: " + ', '.join(sorted(Currencies.CRYPTO_MAP.keys())) + \
                     "\nSupported fiat currencies: " + ', '.join(sorted(Currencies.FIAT_MAP.keys()))

        self.initial_response(return_msg)
        return True

    """Checks that message was from slack and has headers we expect"""
    def basic_header_verification(self):
        for header in self.REQUIRED_HEADERS:
            # Header exists
            if header not in self.headers:
                logging.info(f"Did not receive header {header}")
                return False

            # Header has value expected
            req_val = self.REQUIRED_HEADERS[header]
            if req_val is None:
                continue

            if self.headers[header] != req_val:
                logging.info(f"Header {header} was not \"{req_val}\", instead was \"{self.headers[header]}\"")
                return False

        return True

    """Verify that message was given by slack
    https://api.slack.com/docs/verifying-requests-from-slack"""
    def verify_signature(self, body: str):
        logging.info("Verifying signature")

        # Read headers
        given_sig = self.headers[self.SIG_STRING]
        timestamp = self.headers[self.REQ_TS]

        # Ensure timestamp isn't too old
        unix_now = time.time()
        time_diff = unix_now - int(timestamp)
        if time_diff > self.REPLAY_PREVENTION:
            logging.info(f"Time difference was too large ({time_diff:,.0f} seconds)")
            return False

        # Compute signature
        sig_basestring = self.VERSION + ":" + timestamp + ":" + body
        digest = hmac.new(str.encode(self.SIGNING_SECRET), sig_basestring.encode("utf-8"), digestmod=hashlib.sha256)
        computed_sig = self.VERSION + "=" + digest.hexdigest()

        # Compare
        if hmac.compare_digest(computed_sig, given_sig):
            return True
        else:
            logging.info("Signatures don't match")
            logging.info(f"Given: {given_sig}")
            logging.info(f"Expected: {computed_sig}")

    """Send 200 message back"""
    def initial_response(self, message: str = None):
        self.send_response(200)
        self.end_headers()

        if message is not None:
            self.wfile.write(message.encode())

    """Override default log messaging to do nothing (otherwise would go to stderr
    This is potentially unwanted if output is captured directly to output (although cron needs the process to end)"""
    def log_message(self, format_, *args):
        pass

    @staticmethod
    def run(port):
        server = CustomHTTPServer(('', port), CommandHandler)
        logging.info(f"Web server started on port {port}")
        server.serve_forever()
