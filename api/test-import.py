from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # Try to import requests
            try:
                import requests
                requests_imported = True
                requests_version = requests.__version__
            except ImportError as e:
                requests_imported = False
                requests_version = str(e)
            
            # Check sys.path
            import sys
            
            # Send response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response_data = {
                'success': True,
                'requests_imported': requests_imported,
                'requests_version': requests_version,
                'python_path': sys.path,
                'executable': sys.executable
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