#!/usr/bin/env python3
"""
Simple HTTP Server for BeCoin Economy Dashboard
Serves static files and provides basic API endpoints.
"""

import json
import http.server
import socketserver
from urllib.parse import urlparse, parse_qs
from pathlib import Path

from becoin_economy.engine_v3 import BeCoinEconomy

# Global economy instance
economy = BeCoinEconomy()

class BeCoinHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path

        # API endpoints
        if path == '/api/status':
            self.send_json({"status": "operational", "service": "becoin-economy-v3", "version": "3.0"})

        elif path == '/api/treasury':
            self.send_json(economy.get_api_treasury())

        elif path == '/api/agents':
            self.send_json(economy.get_api_agents())

        elif path == '/api/projects':
            self.send_json(economy.get_api_projects())

        elif path == '/api/pipeline':
            self.send_json(economy.get_api_pipeline())

        elif path == '/api/questions':
            self.send_json(economy.get_api_questions())

        elif path == '/':
            # Serve dashboard
            dashboard_path = Path("dashboard/economy-dashboard.html")
            if dashboard_path.exists():
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(dashboard_path.read_text().encode())
            else:
                self.send_error(404, "Dashboard not found")

        elif path.startswith('/dashboard/'):
            # Serve dashboard files
            file_path = Path("dashboard") / path[len('/dashboard/'):]
            if file_path.exists():
                self.send_response(200)
                if file_path.suffix == '.html':
                    self.send_header('Content-type', 'text/html')
                elif file_path.suffix == '.css':
                    self.send_header('Content-type', 'text/css')
                elif file_path.suffix == '.js':
                    self.send_header('Content-type', 'application/javascript')
                self.end_headers()
                self.wfile.write(file_path.read_bytes())
            else:
                self.send_error(404, "File not found")

        else:
            self.send_error(404, "Endpoint not found")

    def send_json(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())

def run_server(port=8000):
    with socketserver.TCPServer(("", port), BeCoinHandler) as httpd:
        print(f"🤖 BeCoin Economy v3.0 Server")
        print(f"Dashboard: http://localhost:{port}")
        print(f"API: http://localhost:{port}/api/status")
        print("Press Ctrl+C to stop")
        print()

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")
            httpd.shutdown()

if __name__ == "__main__":
    run_server()