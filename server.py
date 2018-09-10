from http.server import BaseHTTPRequestHandler, HTTPServer

class Server(BaseHTTPRequestHandler):
    # POST is for submitting data.
    # noinspection PyPep8Naming
    def do_POST(self):
        print(f"Incoming HTTP POST: {self.path}")
        print(dir(self))

        # Get data
        content_length = int(self.headers['Content-Length'])  # Gets the size of data
        post_data = self.rfile.read(content_length)  # Gets the data itself

        # Parse args
        print("Sending 200 response")
        self.send_response(200)

    @staticmethod
    def run(port):
        server = HTTPServer(('', port), Server)
        print(f"Web server started on port {port}")
        server.serve_forever()
