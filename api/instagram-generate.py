from http.server import BaseHTTPRequestHandler
import json
import requests
import os
from PIL import Image, ImageDraw
import io
import base64
from datetime import datetime, timedelta
import random
from openai import OpenAI
from instagrapi import Client
import tempfile

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
            
            # Check if this is an actual post request
            should_post = data.get('post', False)
            
            # Get configuration from environment variables
            SHOPIFY_SHOP_URL = os.environ.get('SHOPIFY_SHOP_URL', 'your-store.myshopify.com')
            SHOPIFY_ACCESS_TOKEN = os.environ.get('SHOPIFY_ACCESS_TOKEN', 'REDACTED_SHOPIFY_TOKEN')
            OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', 'REDACTED_OPENAI_KEY')
            
            # Instagram credentials
            INSTAGRAM_USERNAME = os.environ.get('INSTAGRAM_USERNAME', '')
            INSTAGRAM_PASSWORD = os.environ.get('INSTAGRAM_PASSWORD', '')
            
            # Initialize OpenAI client only if API key is available
            if OPENAI_API_KEY:
                client = OpenAI(api_key=OPENAI_API_KEY)
            else:
                client = None
            
            # Get posted products
            posted_products = self.get_posted_products()
            
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
                # Skip if already posted
                if str(product['id']) in posted_products:
                    continue
                    
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
                response_body = json.dumps(response_data)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(response_body.encode('utf-8'))
                return
            
            # Select random product
            selected = random.choice(eligible_products)
            product = selected['product']
            complementary_color = selected['complementary_color']
            
            # Create Instagram image
            image_data, image_bytes = self.create_instagram_image(product, complementary_color)
            
            # Generate caption
            caption = self.generate_summary(product, client)
            
            # Add shop link and hashtags to caption
            shop_url = f"https://{SHOPIFY_SHOP_URL}/products/{product['handle']}"
            full_caption = f"{caption}\n\n🛍️ Shop: {shop_url}\n\n#whangāreiartmuseum #nzart #artbooks #museumshop"
            
            # Post to Instagram if requested and credentials are available
            posted = False
            post_url = None
            
            if should_post and INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD:
                try:
                    # Initialize Instagram client
                    ig_client = Client()
                    ig_client.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
                    
                    # Save image to temporary file
                    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
                        # Convert image bytes to PIL Image
                        img = Image.open(io.BytesIO(image_bytes))
                        # Convert to RGB if necessary (Instagram doesn't support transparency)
                        if img.mode != 'RGB':
                            img = img.convert('RGB')
                        img.save(tmp_file, 'JPEG', quality=95)
                        tmp_path = tmp_file.name
                    
                    # Upload photo
                    media = ig_client.photo_upload(tmp_path, full_caption)
                    
                    # Clean up temp file
                    os.unlink(tmp_path)
                    
                    # Mark product as posted
                    self.mark_product_as_posted(product['id'])
                    
                    posted = True
                    post_url = f"https://instagram.com/p/{media.code}"
                    
                except Exception as e:
                    # If posting fails, still return the generated content
                    posted = False
                    post_url = None
            
            # Calculate next post time (tomorrow at 10 AM)
            tomorrow = datetime.now() + timedelta(days=1)
            next_post_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
            
            # Prepare response
            result = {
                'success': True,
                'product_id': product['id'],
                'product_title': product['title'],
                'image_data': image_data,
                'caption': caption,
                'full_caption': full_caption,
                'shop_url': shop_url,
                'next_post_time': next_post_time.isoformat(),
                'complementary_color': complementary_color,
                'posted': posted,
                'post_url': post_url
            }
            
            response_body = json.dumps(result)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(response_body.encode('utf-8'))
            return
            
        except Exception as e:
            import traceback
            error_response = {
                'success': False,
                'error': str(e),
                'traceback': traceback.format_exc()
            }
            response_body = json.dumps(error_response)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(response_body.encode('utf-8'))
            return
    
    def get_posted_products(self):
        """Get list of product IDs that have already been posted"""
        # In a real implementation, you would fetch this from a Shopify metafield
        # or external storage to persist across serverless invocations
        return []
    
    def mark_product_as_posted(self, product_id):
        """Mark a product as posted to Instagram"""
        # In a real implementation, you would update a Shopify metafield
        # or external storage to persist this information
        pass
    
    def create_instagram_image(self, product, complementary_color):
        """Create Instagram square image with product on complementary color background"""
        # Download product image
        image_url = product['images'][0]['src']
        response = requests.get(image_url)
        product_img = Image.open(io.BytesIO(response.content))
        
        # Create square canvas with complementary color
        size = 1080
        background = Image.new('RGB', (size, size), complementary_color)
        
        # Resize product image to fit (80% of canvas)
        product_img.thumbnail((int(size * 0.8), int(size * 0.8)), Image.Resampling.LANCZOS)
        
        # Center the product image
        x = (size - product_img.width) // 2
        y = (size - product_img.height) // 2
        
        # Handle transparency
        if product_img.mode == 'RGBA':
            background.paste(product_img, (x, y), product_img)
        else:
            background.paste(product_img, (x, y))
        
        # Convert to base64 for preview
        buffer = io.BytesIO()
        background.save(buffer, format='PNG')
        buffer.seek(0)
        image_bytes = buffer.getvalue()
        image_data = base64.b64encode(image_bytes).decode('utf-8')
        
        return f"data:image/png;base64,{image_data}", image_bytes
    
    def generate_summary(self, product, client):
        """Generate a 300-word Instagram caption from product description"""
        title = product.get('title', '')
        description = product.get('body_html', '')
        
        # Get configuration from environment variables
        SHOPIFY_SHOP_URL = os.environ.get('SHOPIFY_SHOP_URL', 'your-store.myshopify.com')
        SHOPIFY_ACCESS_TOKEN = os.environ.get('SHOPIFY_ACCESS_TOKEN', 'REDACTED_SHOPIFY_TOKEN')
        
        # Fetch author from metafields
        headers = {
            'X-Shopify-Access-Token': SHOPIFY_ACCESS_TOKEN,
            'Content-Type': 'application/json'
        }
        
        author = None
        try:
            metafields_response = requests.get(
                f'https://{SHOPIFY_SHOP_URL}/admin/api/2024-01/products/{product["id"]}/metafields.json',
                headers=headers
            )
            
            for metafield in metafields_response.json().get('metafields', []):
                if metafield.get('namespace') == 'app-ibp-book' and metafield.get('key') == 'authors':
                    author_value = metafield.get('value')
                    # Parse JSON array if it's a string
                    if author_value and isinstance(author_value, str):
                        try:
                            import json as json_module
                            authors_list = json_module.loads(author_value)
                            if isinstance(authors_list, list):
                                author = ', '.join(authors_list)
                            else:
                                author = author_value
                        except:
                            author = author_value
                    else:
                        author = author_value
                    break
        except:
            # If fetching metafields fails, continue without author
            pass
        
        # Handle None or empty description
        if description is None:
            description = ''
        
        # Strip HTML tags
        import re
        clean_desc = re.sub('<.*?>', '', str(description))
        
        # Format the header
        header = f"{title}"
        if author:
            header = f"{title} ⬤ {author}"
        
        # If no OpenAI client or no description, return just the header and description
        if not client or not clean_desc.strip():
            # Truncate or pad description to approximately 300 words
            words = clean_desc.split()
            if len(words) > 300:
                clean_desc = ' '.join(words[:300])
            return f"{header}\n\n{clean_desc}"
        
        # Generate with OpenAI
        prompt = f"""Take the following product description and rewrite it to be exactly 300 words. 
Keep the content and tone exactly the same - only fix typos, grammar, and improve flow/structure.
Do not editorialize or change the meaning. Do not add hashtags or emojis.

Original description:
{clean_desc}

Rules:
- Keep the same tone and content
- Fix only typos and grammar
- Improve flow and structure if needed
- Make it exactly 300 words
- Do not add any new information
- Do not add hashtags or emojis
- Do not change the meaning or add opinions"""

        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a copy editor. Your job is to fix grammar and adjust word count while keeping the original content and tone intact."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            return f"{header}\n\n{response.choices[0].message.content}"
        except Exception as e:
            # Fallback - just use the original description
            words = clean_desc.split()
            if len(words) > 300:
                clean_desc = ' '.join(words[:300])
            return f"{header}\n\n{clean_desc}"
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers() 