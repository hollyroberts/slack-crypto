from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse as urlparse

class Server(BaseHTTPRequestHandler):
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
        parsed = urlparse.parse_qs(body_data)
        print(parsed['token'][0])

        signature = self.headers[self.SIG_STRING]
        print(f"{self.SIG_STRING}: {signature}")

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

    @staticmethod
    def run(port):
        server = HTTPServer(('', port), Server)
        print(f"Web server started on port {port}")
        server.serve_forever()
