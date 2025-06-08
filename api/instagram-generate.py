from http.server import BaseHTTPRequestHandler
import json
import subprocess
import sys
import os

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # Run the Instagram generation script
            script_path = os.path.join(os.path.dirname(__file__), '..', 'python_scripts', 'generate_instagram_post.py')
            result = subprocess.run([sys.executable, script_path], capture_output=True, text=True)
            
            if result.returncode != 0:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Failed to generate Instagram post', 'details': result.stderr}).encode())
                return
            
            # Parse the output
            output = json.loads(result.stdout)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(output).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers() 