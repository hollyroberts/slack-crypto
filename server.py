from http.server import BaseHTTPRequestHandler, HTTPServer

class Server(BaseHTTPRequestHandler):
    SIG_STRING = "X-Slack-Signature"
    CONTENT_TYPE = "application/x-www-form-urlencoded"

    # POST is for submitting data.
    # noinspection PyPep8Naming
    def do_POST(self):
        print(f"Incoming HTTP POST: {self.path}")

        if not self.verify():
            return

        content_length = int(self.headers['Content-Length'])  # Gets the size of data
        post_data = self.rfile.read(content_length)  # Gets the data itself
        print(post_data)

        # Parse args
        print("Sending 200 response")
        self.send_response(200)

    """Checks that message was from slack and is correct"""
    def verify(self):
        # Content type is application/x-www-form-urlencoded
        content_type = self.headers.get("Content-Type", "None")
        if content_type != self.CONTENT_TYPE:
            print(f"Content type was not {self.CONTENT_TYPE}, instead was {content_type}")

        # Header exists
        if self.SIG_STRING not in self.headers:
            print(f"Did not receive {self.SIG_STRING} header")
            self.send_error(400)
            return False

        signature = self.headers[self.SIG_STRING]
        print(f"{self.SIG_STRING}: {signature}")

        return True

    @staticmethod
    def run(port):
        server = HTTPServer(('', port), Server)
        print(f"Web server started on port {port}")
        server.serve_forever()
