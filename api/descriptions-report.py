from http.server import BaseHTTPRequestHandler
import json
import os
import sys
import subprocess

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # Run the missing descriptions report script
            script_path = os.path.join(os.path.dirname(__file__), '..', 'python_scripts', 'missing_descriptions_report.py')
            result = subprocess.run([sys.executable, script_path], capture_output=True, text=True)
            
            if result.returncode != 0:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': False,
                    'error': 'Failed to generate missing descriptions report',
                    'details': result.stderr
                }).encode())
                return
            
            # Parse the JSON output
            try:
                report = json.loads(result.stdout)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': True,
                    **report
                }).encode())
                
            except json.JSONDecodeError:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': False,
                    'error': 'Failed to parse report data',
                    'details': 'Invalid JSON output from script'
                }).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'success': False,
                'error': str(e)
            }).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers() 