"""Deliberately small, loopback-only HTTP shell; assess and improve its boundary."""
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from core import repair
class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        # Deliberate faults: no body bound, route check, schema or actor binding.
        payload = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        result = json.dumps(repair(payload)).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(result)
if __name__ == '__main__':
    HTTPServer(('127.0.0.1', 8080), Handler).serve_forever()
