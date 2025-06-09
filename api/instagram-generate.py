from http.server import BaseHTTPRequestHandler
import json
import requests
import os

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # Get configuration from environment variables
            SHOPIFY_SHOP_URL = os.environ.get('SHOPIFY_SHOP_URL', 'your-store.myshopify.com')
            SHOPIFY_ACCESS_TOKEN = os.environ.get('SHOPIFY_ACCESS_TOKEN', 'REDACTED_SHOPIFY_TOKEN')
            
            # Fetch products from Shopify
            headers = {
                'X-Shopify-Access-Token': SHOPIFY_ACCESS_TOKEN,
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                f'https://{SHOPIFY_SHOP_URL}/admin/api/2024-01/products.json?limit=10',
                headers=headers
            )
            
            if response.status_code != 200:
                raise Exception(f"Failed to fetch products: {response.status_code}")
            
            products = response.json()['products']
            
            # Count products with images
            products_with_images = [p for p in products if p.get('images')]
            
            # Return success response
            response_data = {
                'success': True,
                'message': 'Successfully fetched products',
                'total_products': len(products),
                'products_with_images': len(products_with_images),
                'test': True
            }
            
            response_body = json.dumps(response_data)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
            self.wfile.write(response_body.encode('utf-8'))
            return
            
        except Exception as e:
            # Return error response
            response_data = {
                'success': False,
                'error': str(e),
                'test': True
            }
            
            response_body = json.dumps(response_data)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
            self.wfile.write(response_body.encode('utf-8'))
            return
    
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write('Hello from Python GET!'.encode('utf-8'))
        return
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        return 