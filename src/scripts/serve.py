#!/usr/bin/env python3
import http.server
import socketserver
import os
from pathlib import Path

PORT = 8000


class StaticHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(Path.cwd()), **kwargs)

    def do_GET(self):
        # Handle root path
        if self.path == '/':
            self.path = 'index.html'
        # Handle static files
        elif self.path.startswith('/static/'):
            self.path = self.path[1:]  # Remove leading slash
        return super().do_GET()


def run_server():
    with socketserver.TCPServer(("", PORT), StaticHandler) as httpd:
        print(f"Serving at http://localhost:{PORT}")
        httpd.serve_forever()


if __name__ == '__main__':
    run_server()
