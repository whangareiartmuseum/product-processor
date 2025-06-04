from http.server import BaseHTTPRequestHandler
import json
import sys
import os
import io
from contextlib import redirect_stdout, redirect_stderr

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # Set environment variables
            os.environ['SHOPIFY_SHOP_URL'] = os.getenv('SHOPIFY_SHOP_URL', '')
            os.environ['SHOPIFY_ACCESS_TOKEN'] = os.getenv('SHOPIFY_ACCESS_TOKEN', '')
            
            # Add python_scripts to path
            script_dir = os.path.join(os.path.dirname(__file__), '../python_scripts')
            if script_dir not in sys.path:
                sys.path.insert(0, script_dir)
            
            # Capture stdout and stderr
            stdout_capture = io.StringIO()
            stderr_capture = io.StringIO()
            logs = []
            
            # Import and run the script
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                try:
                    # Import the module
                    import process_all_colors
                    # Call main with --update-all flag
                    sys.argv = ['process_all_colors.py', '--update-all']
                    process_all_colors.main()
                    success = True
                    error = None
                except Exception as e:
                    success = False
                    error = str(e)
                    import traceback
                    traceback.print_exc()
            
            # Get captured output
            stdout_output = stdout_capture.getvalue()
            stderr_output = stderr_capture.getvalue()
            
            if stdout_output:
                logs.extend([line for line in stdout_output.strip().split('\n') if line])
            if stderr_output:
                logs.extend([f"ERROR: {line}" for line in stderr_output.strip().split('\n') if line])
            
            # Send response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response_data = {
                'success': success,
                'logs': logs,
                'error': error,
                'summary': {
                    'message': 'Color extraction for all products completed',
                    'processType': 'all_products'
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
                'logs': ['Failed to run color extraction for all products']
            }
            
            self.wfile.write(json.dumps(response_data).encode())
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers() 