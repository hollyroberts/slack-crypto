import hashlib
from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse as urlparse
import hmac

class Server(BaseHTTPRequestHandler):
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
        print("Sending 200 response")
        self.send_response(200)

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
