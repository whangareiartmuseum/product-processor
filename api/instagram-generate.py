from http.server import BaseHTTPRequestHandler
import json
import requests
import os
from datetime import datetime, timedelta
import random

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # Parse request body
            content_length = self.headers.get('Content-Length')
            if content_length:
                post_data = self.rfile.read(int(content_length))
                if post_data:
                    try:
                        data = json.loads(post_data.decode('utf-8'))
                    except json.JSONDecodeError:
                        data = {}
                else:
                    data = {}
            else:
                data = {}
            
            # Get configuration from environment variables
            SHOPIFY_SHOP_URL = os.environ.get('SHOPIFY_SHOP_URL', '')
            SHOPIFY_ACCESS_TOKEN = os.environ.get('SHOPIFY_ACCESS_TOKEN', '')
            
            # Fetch eligible products
            headers = {
                'X-Shopify-Access-Token': SHOPIFY_ACCESS_TOKEN,
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                f'https://{SHOPIFY_SHOP_URL}/admin/api/2024-01/products.json?limit=250',
                headers=headers
            )
            
            products = response.json()['products']
            
            # Filter eligible products
            eligible_products = []
            for product in products:
                # Skip if no images
                if not product.get('images'):
                    continue
                
                # Skip if out of stock
                total_inventory = sum(variant.get('inventory_quantity', 0) for variant in product.get('variants', []))
                if total_inventory <= 0:
                    continue
                    
                # Check for complementary color metafield
                metafields_response = requests.get(
                    f'https://{SHOPIFY_SHOP_URL}/admin/api/2024-01/products/{product["id"]}/metafields.json',
                    headers=headers
                )
                
                has_complementary_color = False
                complementary_color = None
                
                for metafield in metafields_response.json().get('metafields', []):
                    if metafield.get('namespace') == 'wam_color_manager' and metafield.get('key') == 'complementary_color':
                        has_complementary_color = True
                        complementary_color = metafield.get('value')
                        break
                
                if has_complementary_color:
                    eligible_products.append({
                        'product': product,
                        'complementary_color': complementary_color
                    })
            
            if not eligible_products:
                response_data = {
                    'success': False,
                    'error': 'No eligible products found for Instagram post'
                }
            else:
                # Select random product
                selected = random.choice(eligible_products)
                product = selected['product']
                complementary_color = selected['complementary_color']
                
                # Calculate next post time (tomorrow at 10 AM)
                tomorrow = datetime.now() + timedelta(days=1)
                next_post_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
                
                # Prepare response WITHOUT image generation for now
                response_data = {
                    'success': True,
                    'product_id': product['id'],
                    'product_title': product['title'],
                    'image_data': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==',  # 1x1 placeholder
                    'caption': f"{product['title']}\n\nTesting Instagram functionality",
                    'full_caption': f"{product['title']}\n\nTesting Instagram functionality\n\n🛍️ Shop: https://{SHOPIFY_SHOP_URL}/products/{product['handle']}",
                    'shop_url': f"https://{SHOPIFY_SHOP_URL}/products/{product['handle']}",
                    'next_post_time': next_post_time.isoformat(),
                    'complementary_color': complementary_color,
                    'posted': False,
                    'post_url': None,
                    'test': True,
                    'eligible_count': len(eligible_products)
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
            import traceback
            response_data = {
                'success': False,
                'error': str(e),
                'traceback': traceback.format_exc()
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
        self.wfile.write('Instagram endpoint is working!'.encode('utf-8'))
        return
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        return 