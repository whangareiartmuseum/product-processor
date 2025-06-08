#!/usr/bin/env python3
import requests
import json
import os
import sys
from PIL import Image, ImageDraw
import io
import base64
from datetime import datetime, timedelta
import random
from openai import OpenAI

# Get configuration from environment variables
SHOPIFY_SHOP_URL = os.environ.get('SHOPIFY_SHOP_URL', 'your-store.myshopify.com')
SHOPIFY_ACCESS_TOKEN = os.environ.get('SHOPIFY_ACCESS_TOKEN', 'REDACTED_SHOPIFY_TOKEN')
# Note: Please set OPENAI_API_KEY as an environment variable
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Initialize OpenAI client only if API key is available
if OPENAI_API_KEY:
    client = OpenAI(api_key=OPENAI_API_KEY)
else:
    client = None

def get_posted_products():
    """Get list of product IDs that have already been posted"""
    posted_file = os.path.join(script_dir, 'posted_products.json')
    if os.path.exists(posted_file):
        with open(posted_file, 'r') as f:
            return json.load(f)
    return []

def save_posted_product(product_id):
    """Save product ID to the list of posted products"""
    posted_file = os.path.join(script_dir, 'posted_products.json')
    posted = get_posted_products()
    if product_id not in posted:
        posted.append(product_id)
        with open(posted_file, 'w') as f:
            json.dump(posted, f)

def get_random_product():
    """Get a random product that hasn't been posted yet"""
    headers = {
        'X-Shopify-Access-Token': SHOPIFY_ACCESS_TOKEN,
        'Content-Type': 'application/json'
    }
    
    # Get all products with complementary color metafield
    url = f"https://{SHOPIFY_SHOP_URL}/admin/api/2024-01/products.json?fields=id,title,body_html,images,status,variants&limit=250"
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        raise Exception(f"Failed to fetch products: {response.status_code}")
    
    products = response.json()['products']
    
    # Filter out products that have been posted or are not active
    posted_ids = get_posted_products()
    available_products = []
    
    for product in products:
        # Skip if already posted or not active
        if str(product['id']) in posted_ids or product['status'] != 'active':
            continue
            
        # Check if product is in stock
        in_stock = any(variant.get('inventory_quantity', 0) > 0 for variant in product.get('variants', []))
        if not in_stock:
            continue
            
        # Get metafields to check for complementary color
        metafields_url = f"https://{SHOPIFY_SHOP_URL}/admin/api/2024-01/products/{product['id']}/metafields.json"
        metafields_response = requests.get(metafields_url, headers=headers)
        
        if metafields_response.status_code == 200:
            metafields = metafields_response.json()['metafields']
            has_complementary = any(mf['namespace'] == 'wam_color_manager' and mf['key'] == 'complementary_color' for mf in metafields)
            if has_complementary and product.get('images'):
                available_products.append(product)
    
    if not available_products:
        raise Exception("No available products to post")
    
    # Select random product
    selected_product = random.choice(available_products)
    
    # Get full product details including metafields
    product_id = selected_product['id']
    metafields_url = f"https://{SHOPIFY_SHOP_URL}/admin/api/2024-01/products/{product_id}/metafields.json"
    metafields_response = requests.get(metafields_url, headers=headers)
    
    metafields = {}
    if metafields_response.status_code == 200:
        for mf in metafields_response.json()['metafields']:
            if mf['namespace'] == 'wam_color_manager':
                metafields[mf['key']] = mf['value']
    
    selected_product['metafields'] = metafields
    return selected_product

def hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def create_instagram_image(product):
    """Create Instagram post image with product on complementary color background"""
    # Get complementary color
    comp_color = product['metafields'].get('complementary_color', '#808080')
    rgb_color = hex_to_rgb(comp_color)
    
    # Create square canvas (1080x1080 for Instagram)
    canvas_size = 1080
    canvas = Image.new('RGB', (canvas_size, canvas_size), rgb_color)
    
    # Get product image
    if product.get('images'):
        image_url = product['images'][0]['src']
        response = requests.get(image_url)
        product_img = Image.open(io.BytesIO(response.content))
        
        # Convert to RGBA if needed
        if product_img.mode != 'RGBA':
            product_img = product_img.convert('RGBA')
        
        # Calculate size to fit in center (80% of canvas)
        max_size = int(canvas_size * 0.8)
        product_img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        
        # Center the image
        x = (canvas_size - product_img.width) // 2
        y = (canvas_size - product_img.height) // 2
        
        # Paste product image onto canvas
        canvas.paste(product_img, (x, y), product_img if product_img.mode == 'RGBA' else None)
    
    # Convert to base64 for web display
    buffered = io.BytesIO()
    canvas.save(buffered, format="PNG")
    img_base64 = base64.b64encode(buffered.getvalue()).decode()
    
    return f"data:image/png;base64,{img_base64}"

def generate_summary(product):
    """Generate a 300-word Instagram caption from product description"""
    description = product.get('body_html', '')
    
    # Handle None or empty description
    if description is None:
        description = ''
    
    # Strip HTML tags
    import re
    clean_desc = re.sub('<.*?>', '', str(description))
    
    # Check if OpenAI API key is available
    if not OPENAI_API_KEY:
        # Fallback caption when API key is not available
        title = product['title']
        desc_preview = clean_desc[:200] + "..." if len(clean_desc) > 200 else clean_desc
        
        return f"""Discover the beauty of {title} at Whangārei Art Museum! 

{desc_preview}

This unique piece from our collection represents the rich artistic heritage of our region. Each item in our museum store has been carefully selected to bring a piece of our cultural experience into your everyday life.

Whether you're a collector, art enthusiast, or looking for that perfect gift, this item offers a tangible connection to the creative spirit that defines our museum. The quality craftsmanship and attention to detail make it a treasured addition to any collection.

Visit us at Whangārei Art Museum to explore our full range of products and immerse yourself in the vibrant arts scene of Northland. Our knowledgeable staff are always happy to share the stories behind each piece and help you find something that speaks to you.

Supporting our museum store directly contributes to our exhibitions, educational programs, and community initiatives. Every purchase helps us continue our mission of making art accessible to all.

#WhangāreiArtMuseum #MuseumStore #ArtLovers #NewZealandArt #Northland #CulturalHeritage #ArtCollector #MuseumGift #LocalArt #SupportTheArts #ArtisticExpression #MuseumLife #CreativeNZ #ArtCommunity"""
    
    prompt = f"""Create an engaging Instagram caption for this product. The caption should be exactly 300 words.

Product: {product['title']}
Description: {clean_desc}

Guidelines:
- Make it conversational and engaging
- Include relevant hashtags at the end
- Focus on the benefits and appeal of the product
- Use a friendly, approachable tone
- Make it suitable for Instagram's audience
- Do not use emojis in the main text, only at the very end if appropriate

Write exactly 300 words."""

    try:
        if client:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a social media content creator specializing in art and museum products."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            
            return response.choices[0].message.content
        else:
            raise Exception("OpenAI API key not configured")
    except Exception as e:
        # Return fallback caption on error
        title = product['title']
        return f"""Discover the beauty of {title} at Whangārei Art Museum! 

This unique piece from our collection represents the rich artistic heritage of our region. Each item in our museum store has been carefully selected to bring a piece of our cultural experience into your everyday life.

Visit us at Whangārei Art Museum to explore our full range of products. Supporting our museum store directly contributes to our exhibitions and community programs.

#WhangāreiArtMuseum #MuseumStore #ArtLovers #NewZealandArt #Northland"""

def get_next_post_time():
    """Calculate next post time (tomorrow at 10 AM)"""
    now = datetime.now()
    tomorrow = now + timedelta(days=1)
    next_post = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
    
    # If it's before 10 AM today, post today
    today_10am = now.replace(hour=10, minute=0, second=0, microsecond=0)
    if now < today_10am:
        next_post = today_10am
    
    return next_post

def main():
    try:
        # Get random product
        product = get_random_product()
        
        # Generate image
        image_data = create_instagram_image(product)
        
        # Generate caption
        caption = generate_summary(product)
        
        # Get next post time
        next_post_time = get_next_post_time()
        
        # Prepare result
        result = {
            'success': True,
            'product_id': product['id'],
            'product_title': product['title'],
            'image_data': image_data,
            'caption': caption,
            'next_post_time': next_post_time.isoformat(),
            'complementary_color': product['metafields'].get('complementary_color', '#808080')
        }
        
        print(json.dumps(result))
        
    except Exception as e:
        print(json.dumps({
            'success': False,
            'error': str(e)
        }))

if __name__ == "__main__":
    main() 