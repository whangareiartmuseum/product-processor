#!/usr/bin/env python3
"""
Update products with poor color contrast ratios.
"""

import requests
import json
import os
import time
from tqdm import tqdm
from PIL import Image
from io import BytesIO
from color_extractor_fixed import get_dominant_color, get_complementary_color, generate_text_color_from_dominant, get_contrast_ratio

# Get Shopify API Configuration
def get_shopify_config():
    """Get Shopify configuration from environment variables."""
    shop_url = os.getenv('SHOPIFY_SHOP_URL')
    access_token = os.getenv('SHOPIFY_ACCESS_TOKEN')
    
    if not shop_url or not access_token:
        raise ValueError("Missing required environment variables: SHOPIFY_SHOP_URL and/or SHOPIFY_ACCESS_TOKEN")
    
    graphql_url = f"https://{shop_url}/admin/api/2024-01/graphql.json"
    return shop_url, access_token, graphql_url

def get_all_products_with_colors(cursor=None, products=None):
    """Get all products from the store with color metafields."""
    if products is None:
        products = []
        
    shop_url, access_token, graphql_url = get_shopify_config()
    
    headers = {
        'X-Shopify-Access-Token': access_token,
        'Content-Type': 'application/json'
    }
    
    query = """
    query GetProducts($cursor: String) {
        products(first: 50, after: $cursor) {
            pageInfo {
                hasNextPage
                endCursor
            }
            edges {
                node {
                    id
                    title
                    handle
                    featuredImage {
                        url
                    }
                    images(first: 5) {
                        edges {
                            node {
                                url
                            }
                        }
                    }
                    metafields(first: 30) {
                        edges {
                            node {
                                namespace
                                key
                                value
                            }
                        }
                    }
                }
            }
        }
    }
    """
    
    variables = {}
    if cursor:
        variables["cursor"] = cursor
    
    payload = {
        "query": query,
        "variables": variables
    }
    
    response = requests.post(graphql_url, headers=headers, json=payload)
    
    if response.status_code != 200:
        print(f"Failed to get products: {response.status_code}")
        return products
    
    data = response.json()
    product_edges = data.get('data', {}).get('products', {}).get('edges', [])
    products.extend([edge['node'] for edge in product_edges])
    
    # Check if there are more pages
    page_info = data.get('data', {}).get('products', {}).get('pageInfo', {})
    has_next_page = page_info.get('hasNextPage', False)
    
    if has_next_page:
        end_cursor = page_info.get('endCursor')
        time.sleep(0.5)  # Rate limiting
        return get_all_products_with_colors(cursor=end_cursor, products=products)
    
    return products

def check_color_metafields(product):
    """Check which color metafields exist for a product."""
    metafields = product.get('metafields', {}).get('edges', [])
    
    color_status = {
        'dominant_color': {'exists': False, 'value': None},
        'complementary_color': {'exists': False, 'value': None},
        'text_color': {'exists': False, 'value': None}
    }
    
    for metafield_edge in metafields:
        metafield = metafield_edge.get('node', {})
        namespace = metafield.get('namespace', '')
        key = metafield.get('key', '')
        value = metafield.get('value', '')
        
        if namespace == 'wam_color_manager':
            if key == 'dominant_color' and value:
                color_status['dominant_color'] = {'exists': True, 'value': value}
            elif key == 'complementary_color' and value:
                color_status['complementary_color'] = {'exists': True, 'value': value}
            elif key == 'text_color' and value:
                color_status['text_color'] = {'exists': True, 'value': value}
    
    return color_status

def get_product_image_url(product):
    """Get the first available image URL for a product."""
    featured_image = product.get('featuredImage')
    if featured_image:
        return featured_image.get('url')
    
    images = product.get('images', {}).get('edges', [])
    if images:
        return images[0].get('node', {}).get('url')
    
    return None

def download_image(url):
    """Download image from URL and return PIL Image object."""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return Image.open(BytesIO(response.content))
    except Exception as e:
        print(f"Error downloading image: {e}")
    return None

def update_product_color_metafields(product_id, dominant_color, complementary_color, text_color):
    """Update all three color metafields for a product."""
    shop_url, access_token, graphql_url = get_shopify_config()
    
    headers = {
        'X-Shopify-Access-Token': access_token,
        'Content-Type': 'application/json'
    }
    
    mutation = """
    mutation UpdateProductMetafields($productId: ID!, $metafields: [MetafieldInput!]!) {
        productUpdate(
            input: {
                id: $productId
                metafields: $metafields
            }
        ) {
            product {
                id
            }
            userErrors {
                field
                message
            }
        }
    }
    """
    
    variables = {
        "productId": product_id,
        "metafields": [
            {
                "namespace": "wam_color_manager",
                "key": "dominant_color",
                "value": dominant_color,
                "type": "color"
            },
            {
                "namespace": "wam_color_manager",
                "key": "complementary_color",
                "value": complementary_color,
                "type": "color"
            },
            {
                "namespace": "wam_color_manager",
                "key": "text_color",
                "value": text_color,
                "type": "color"
            }
        ]
    }
    
    payload = {
        "query": mutation,
        "variables": variables
    }
    
    response = requests.post(graphql_url, headers=headers, json=payload)
    
    if response.status_code != 200:
        return False
    
    data = response.json()
    
    if 'errors' in data:
        return False
    
    user_errors = data.get('data', {}).get('productUpdate', {}).get('userErrors', [])
    if user_errors:
        return False
    
    return True

def process_product(product):
    """Process a single product and extract/update colors."""
    product_id = product.get('id')
    
    # Get image URL
    image_url = get_product_image_url(product)
    if not image_url:
        return False, "No image found"
    
    try:
        # Download image
        image = download_image(image_url)
        if not image:
            return False, "Failed to download image"
        
        # Extract dominant colors
        dominant_colors = get_dominant_color(image, num_colors=1)
        if not dominant_colors:
            return False, "Failed to extract colors"
        
        # Get the primary dominant color
        dominant_color = dominant_colors[0]['hex']
        
        # Generate complementary color
        complementary_color = get_complementary_color(dominant_color)
        
        # Generate text color based on contrast requirements
        text_color = generate_text_color_from_dominant(dominant_color, complementary_color)
        comp_text_contrast = get_contrast_ratio(complementary_color, text_color)
        
        # Update metafields
        if update_product_color_metafields(product_id, dominant_color, complementary_color, text_color):
            return True, f"Updated colors (Comp↔Text: {comp_text_contrast:.2f}:1)"
        else:
            return False, "Failed to update metafields"
            
    except Exception as e:
        return False, f"Error: {str(e)}"

def find_poor_contrast_products():
    """Find all products with poor color contrast."""
    print("\n🔍 Finding products with poor contrast...")
    print("=" * 60)
    
    # Fetch all products
    print("Fetching all products from Shopify...")
    all_products = get_all_products_with_colors()
    
    poor_contrast_products = []
    
    print("Analyzing contrast ratios...")
    for product in tqdm(all_products, desc="Analyzing"):
        # Check color metafields
        color_status = check_color_metafields(product)
        
        # Only process if all color fields exist
        if all(status['exists'] for status in color_status.values()):
            complementary_color = color_status['complementary_color']['value']
            text_color = color_status['text_color']['value']
            
            # Calculate contrast ratio
            contrast_ratio = get_contrast_ratio(complementary_color, text_color)
            
            # Check if it fails WCAG AA standard (< 4.5:1)
            if contrast_ratio < 4.5:
                poor_contrast_products.append({
                    'product': product,
                    'contrast_ratio': contrast_ratio,
                    'title': product.get('title', 'Unknown')
                })
    
    return poor_contrast_products

def main():
    """Main function to update products with poor contrast."""
    print("\n🎨 WAM Color Manager - Update Poor Contrast Products")
    print("=" * 60)
    
    # Find products with poor contrast
    poor_contrast_products = find_poor_contrast_products()
    
    if not poor_contrast_products:
        print("\n✨ Great news! No products with poor contrast found.")
        print("All products meet WCAG AA standards (4.5:1 or better).")
        return
    
    print(f"\n⚠️  Found {len(poor_contrast_products)} products with poor contrast (<4.5:1)")
    
    # Show worst offenders
    print("\nWorst contrast ratios:")
    sorted_products = sorted(poor_contrast_products, key=lambda x: x['contrast_ratio'])
    for i, item in enumerate(sorted_products[:5]):
        print(f"   {i+1}. {item['title'][:50]} - {item['contrast_ratio']:.2f}:1")
    
    if len(sorted_products) > 5:
        print(f"   ... and {len(sorted_products) - 5} more")
    
    # Confirm update
    confirm = input(f"\n🔄 Update all {len(poor_contrast_products)} products? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Update cancelled.")
        return
    
    # Process each product
    successful = 0
    failed = 0
    
    print(f"\n🎨 Processing {len(poor_contrast_products)} products...")
    
    for item in tqdm(poor_contrast_products, desc="Updating"):
        product = item['product']
        old_ratio = item['contrast_ratio']
        
        tqdm.write(f"\n📦 {item['title']}")
        tqdm.write(f"   Old contrast: {old_ratio:.2f}:1")
        
        success, message = process_product(product)
        
        if success:
            successful += 1
            tqdm.write(f"   ✅ {message}")
        else:
            failed += 1
            tqdm.write(f"   ❌ {message}")
        
        # Rate limiting
        time.sleep(0.5)
    
    # Summary
    print("\n" + "=" * 60)
    print("🎉 UPDATE COMPLETE")
    print("=" * 60)
    print(f"✅ Successfully updated: {successful} products")
    print(f"❌ Failed updates: {failed} products")
    print(f"📊 Total processed: {len(poor_contrast_products)} products")
    
    if successful > 0:
        print(f"\n💡 Tip: Run the contrast report again to verify improvements!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Process interrupted by user.")
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc() 