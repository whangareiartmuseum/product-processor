from http.server import BaseHTTPRequestHandler
import json
import os
import sys

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # Read the request body
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            if 'productId' not in data:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Product ID is required'}).encode())
                return
            
            product_id = data['productId']
            
            # Update the posted products file
            posted_file = os.path.join(os.path.dirname(__file__), '..', 'python_scripts', 'posted_products.json')
            
            posted = []
            try:
                with open(posted_file, 'r') as f:
                    posted = json.load(f)
            except FileNotFoundError:
                # File doesn't exist yet, that's okay
                pass
            
            if str(product_id) not in posted:
                posted.append(str(product_id))
                with open(posted_file, 'w') as f:
                    json.dump(posted, f, indent=2)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'success': True, 'posted': posted}).encode())
            
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