from http.server import BaseHTTPRequestHandler
import json
import sys
import os
import subprocess

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # Set environment variables
            os.environ['SHOPIFY_SHOP_URL'] = os.getenv('SHOPIFY_SHOP_URL', '')
            os.environ['SHOPIFY_ACCESS_TOKEN'] = os.getenv('SHOPIFY_ACCESS_TOKEN', '')
            
            # Path to the script
            script_path = os.path.join(os.path.dirname(__file__), '../../python_scripts/process_all_colors.py')
            
            # Run the script with report flags
            result = subprocess.run(
                [sys.executable, script_path, '--report', '--contrast-type', 'comp_text'],
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
                    'message': 'Color contrast report generated',
                    'processType': 'contrast_report',
                    'reportType': 'complementary_vs_text'
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
                'logs': ['Failed to run contrast report']
            }
            
            self.wfile.write(json.dumps(response_data).encode())
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers() 