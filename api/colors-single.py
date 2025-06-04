from http.server import BaseHTTPRequestHandler
import json
import sys
import os
import io
from contextlib import redirect_stdout, redirect_stderr

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
                    # Import required modules
                    import process_single_product
                    
                    # Process the product directly without confirmation
                    print(f"\n🔍 Processing product: {product_input}")
                    print("=" * 60)
                    
                    # Get product
                    product = process_single_product.get_product_by_id(product_input)
                    if not product:
                        raise Exception(f"Product not found: {product_input}")
                    
                    print(f"✅ Found product: {product.get('title', 'Unknown')}")
                    
                    # Get image URL
                    featured_image = product.get('featuredImage', {})
                    image_url = featured_image.get('url') if featured_image else None
                    
                    if not image_url:
                        images = product.get('images', {}).get('edges', [])
                        if images:
                            image_url = images[0].get('node', {}).get('url')
                    
                    if not image_url:
                        raise Exception("No product image found")
                    
                    # Download and process image
                    print("\n🎨 Extracting colors...")
                    image = process_single_product.download_image(image_url)
                    if not image:
                        raise Exception("Failed to download image")
                    
                    # Import color extractor functions
                    from color_extractor_fixed import get_dominant_color, get_complementary_color, generate_text_color_from_dominant, get_contrast_ratio
                    
                    # Extract colors
                    dominant_colors = get_dominant_color(image, num_colors=1)
                    if not dominant_colors:
                        raise Exception("Failed to extract dominant color")
                    
                    dominant_color = dominant_colors[0]['hex']
                    complementary_color = get_complementary_color(dominant_color)
                    text_color = generate_text_color_from_dominant(dominant_color, complementary_color)
                    
                    # Calculate contrasts
                    comp_text_contrast = get_contrast_ratio(complementary_color, text_color)
                    
                    print(f"\n✨ COLORS GENERATED:")
                    print(f"   Dominant: {dominant_color}")
                    print(f"   Complementary: {complementary_color}")
                    print(f"   Text: {text_color}")
                    print(f"   Complementary↔Text contrast: {comp_text_contrast:.2f}:1")
                    
                    # Update metafields
                    print("\n📤 Updating metafields...")
                    if process_single_product.update_product_colors(product.get('id'), dominant_color, complementary_color, text_color):
                        print("✅ Colors successfully saved!")
                        success = True
                        error = None
                    else:
                        raise Exception("Failed to save colors")
                        
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