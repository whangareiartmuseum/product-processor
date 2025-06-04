from http.server import BaseHTTPRequestHandler
import json
import sys
import os

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # Add the python_scripts directory to the path
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../python_scripts'))
            
            # Set environment variables
            os.environ['SHOPIFY_SHOP_URL'] = os.getenv('SHOPIFY_SHOP_URL', '')
            os.environ['SHOPIFY_ACCESS_TOKEN'] = os.getenv('SHOPIFY_ACCESS_TOKEN', '')
            
            # Import and run the script
            import io
            from contextlib import redirect_stdout, redirect_stderr
            
            stdout_capture = io.StringIO()
            stderr_capture = io.StringIO()
            logs = []
            
            # Import main function from process_all_colors
            from process_all_colors import main
            
            # Run with output capture
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                try:
                    main()  # No args means process only missing
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
                    'message': 'Color extraction for products missing metadata completed',
                    'processType': 'missing_only'
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
                'logs': ['Failed to run color extraction for missing products']
            }
            
            self.wfile.write(json.dumps(response_data).encode())
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers() 