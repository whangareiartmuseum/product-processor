from http.server import BaseHTTPRequestHandler
import json
import os
import requests

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # Get environment variables
            SHOP_URL = os.getenv('SHOPIFY_SHOP_URL', 'your-store.myshopify.com')
            ACCESS_TOKEN = os.getenv('SHOPIFY_ACCESS_TOKEN', 'REDACTED_SHOPIFY_TOKEN')
            GRAPHQL_URL = f"https://{SHOP_URL}/admin/api/2024-01/graphql.json"
            
            headers = {
                'X-Shopify-Access-Token': ACCESS_TOKEN,
                'Content-Type': 'application/json'
            }
            
            query = """
            query GetProducts {
                products(first: 10) {
                    edges {
                        node {
                            id
                            title
                            metafields(first: 50) {
                                edges {
                                    node {
                                        id
                                        namespace
                                        key
                                        value
                                        type
                                    }
                                }
                            }
                        }
                    }
                }
            }
            """
            
            payload = {"query": query}
            
            # Make the GraphQL request
            response = requests.post(GRAPHQL_URL, headers=headers, json=payload)
            
            logs = []
            
            if response.status_code != 200:
                logs.append(f"Failed to get products: {response.status_code}")
                success = False
            else:
                data = response.json()
                products = data.get('data', {}).get('products', {}).get('edges', [])
                
                logs.append("🔍 Inspecting Metafield Structure")
                logs.append("=" * 80)
                
                for product_edge in products:
                    product = product_edge.get('node', {})
                    title = product.get('title', 'Unknown')
                    metafields = product.get('metafields', {}).get('edges', [])
                    
                    # Look for color-related metafields
                    color_fields = []
                    for mf_edge in metafields:
                        mf = mf_edge.get('node', {})
                        namespace = mf.get('namespace', '')
                        key = mf.get('key', '')
                        
                        if ('color' in key.lower() or 'colour' in key.lower() or 
                            namespace == 'wam_color_manager' or namespace == 'custom'):
                            color_fields.append(mf)
                    
                    if color_fields:
                        logs.append(f"\n📦 {title}")
                        for mf in color_fields:
                            namespace = mf.get('namespace', '')
                            key = mf.get('key', '')
                            value = mf.get('value', '')
                            mf_type = mf.get('type', '')
                            mf_id = mf.get('id', '')
                            
                            logs.append(f"   • {namespace}.{key}")
                            logs.append(f"     Type: {mf_type}")
                            logs.append(f"     ID: {mf_id}")
                            
                            # If it's JSON, try to parse and pretty print
                            if mf_type == 'json' and value:
                                try:
                                    parsed = json.loads(value)
                                    logs.append(f"     Value (parsed JSON):")
                                    logs.append(f"     {json.dumps(parsed, indent=6)}")
                                except:
                                    logs.append(f"     Value: {value[:200]}...")
                            else:
                                logs.append(f"     Value: {value[:200] if len(value) > 200 else value}")
                
                success = True
            
            # Send response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response_data = {
                'success': success,
                'logs': logs,
                'error': None if success else 'Failed to inspect metafields',
                'summary': {
                    'message': 'Metafields inspection completed',
                    'processType': 'inspect_metafields'
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
                'logs': ['Failed to inspect metafields: ' + str(e)]
            }
            
            self.wfile.write(json.dumps(response_data).encode())
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers() 