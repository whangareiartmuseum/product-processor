from http.server import BaseHTTPRequestHandler
import json
import sys
import os
import subprocess

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # Read request body
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            request_data = json.loads(post_data.decode('utf-8'))
            
            product_input = request_data.get('input', '')
            
            if not product_input:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                response_data = {
                    'success': False,
                    'error': 'Product ID or handle is required'
                }
                self.wfile.write(json.dumps(response_data).encode())
                return
            
            # Set environment variables
            os.environ['SHOPIFY_SHOP_URL'] = os.getenv('SHOPIFY_SHOP_URL', '')
            os.environ['SHOPIFY_ACCESS_TOKEN'] = os.getenv('SHOPIFY_ACCESS_TOKEN', '')
            
            # Path to the script
            script_path = os.path.join(os.path.dirname(__file__), '../../python_scripts/process_single_product.py')
            
            # Run the script with product input
            result = subprocess.run(
                [sys.executable, script_path, product_input],
                capture_output=True,
                text=True,
                env=os.environ
            )
            
            # Parse output
            logs = []
            if result.stdout:
                logs.extend(result.stdout.strip().split('\n'))
            if result.stderr:
                logs.extend([f"ERROR: {line}" for line in result.stderr.strip().split('\n') if line])
            
            success = result.returncode == 0
            
            # Send response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response_data = {
                'success': success,
                'logs': logs,
                'error': None if success else 'Process failed',
                'summary': {
                    'message': f'Color extraction for product "{product_input}" completed',
                    'processType': 'single_product',
                    'productId': product_input
                }
            }
            
            self.wfile.write(json.dumps(response_data).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response_data = {
                'success': False,
                'error': str(e),
                'logs': ['Failed to process single product']
            }
            
            self.wfile.write(json.dumps(response_data).encode())
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers() 