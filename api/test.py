from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # Test basic Python functionality
            import sys
            python_version = sys.version
            
            # Test if we can access environment variables
            import os
            has_shopify = 'SHOPIFY_SHOP_URL' in os.environ
            
            # Send response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response_data = {
                'success': True,
                'python_version': python_version,
                'has_shopify_env': has_shopify,
                'working_directory': os.getcwd(),
                'api_dir_contents': os.listdir(os.path.dirname(__file__)) if os.path.dirname(__file__) else 'Unable to determine',
                'root_contents': os.listdir('/var/task') if os.path.exists('/var/task') else 'Not in Vercel'
            }
            
            self.wfile.write(json.dumps(response_data).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response_data = {
                'success': False,
                'error': str(e)
            }
            
            self.wfile.write(json.dumps(response_data).encode())
    
    def do_POST(self):
        self.do_GET() 