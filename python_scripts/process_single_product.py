#!/usr/bin/env python3
"""
Process and update colors for a single product.
"""

import requests
import json
import sys
import os
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

def get_product_by_id(product_id):
    """Get a single product by ID."""
    shop_url, access_token, graphql_url = get_shopify_config()
    
    headers = {
        'X-Shopify-Access-Token': access_token,
        'Content-Type': 'application/json'
    }
    
    # Ensure proper ID format
    if product_id.isdigit():
        product_id = f"gid://shopify/Product/{product_id}"
    
    query = """
    query GetProduct($id: ID!) {
        product(id: $id) {
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
            metafields(first: 20) {
                edges {
                    node {
                        namespace
                        key
                        value
                        type
                    }
                }
            }
        }
    }
    """
    
    variables = {"id": product_id}
    payload = {"query": query, "variables": variables}
    
    response = requests.post(graphql_url, headers=headers, json=payload)
    
    if response.status_code != 200:
        print(f"❌ Failed to fetch product: HTTP {response.status_code}")
        return None
    
    data = response.json()
    
    if 'errors' in data:
        print(f"❌ GraphQL error: {data['errors'][0]['message']}")
        return None
    
    return data.get('data', {}).get('product')

def download_image(url):
    """Download an image from URL."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return Image.open(BytesIO(response.content))
    except Exception as e:
        print(f"❌ Failed to download image: {str(e)}")
        return None

def update_product_colors(product_id, dominant_color, complementary_color, text_color):
    """Update the color metafields for a product."""
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
                title
                metafields(first: 10) {
                    edges {
                        node {
                            namespace
                            key
                            value
                        }
                    }
                }
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
    
    payload = {"query": mutation, "variables": variables}
    
    response = requests.post(graphql_url, headers=headers, json=payload)
    
    if response.status_code != 200:
        print(f"❌ Failed to update metafields: HTTP {response.status_code}")
        return False
    
    data = response.json()
    
    if 'errors' in data:
        print(f"❌ GraphQL error: {data['errors'][0]['message']}")
        return False
    
    user_errors = data.get('data', {}).get('productUpdate', {}).get('userErrors', [])
    if user_errors:
        print(f"❌ User error: {user_errors[0]['message']}")
        return False
    
    return True

def process_product(product_id_or_handle):
    """Process and update colors for a single product."""
    print(f"\n🔍 Processing product: {product_id_or_handle}")
    print("=" * 60)
    
    # Get product
    product = get_product_by_id(product_id_or_handle)
    if not product:
        print(f"❌ Product not found: {product_id_or_handle}")
        return
    
    print(f"✅ Found product: {product.get('title', 'Unknown')}")
    print(f"   Handle: {product.get('handle', 'N/A')}")
    print(f"   ID: {product.get('id', 'N/A')}")
    
    # Check current metafields
    print("\n📊 Current color metafields:")
    metafields = product.get('metafields', {}).get('edges', [])
    color_fields = {}
    
    for mf_edge in metafields:
        mf = mf_edge.get('node', {})
        namespace = mf.get('namespace', '')
        key = mf.get('key', '')
        value = mf.get('value', '')
        
        if namespace == 'wam_color_manager' and key in ['dominant_color', 'complementary_color', 'text_color']:
            color_fields[key] = value
            print(f"   • {key}: {value}")
        elif namespace == 'custom' and 'color' in key.lower():
            print(f"   • [custom] {key}: {value}")
    
    if not color_fields:
        print("   No color metafields found")
    
    # Get image
    featured_image = product.get('featuredImage', {})
    image_url = featured_image.get('url') if featured_image else None
    
    if not image_url:
        images = product.get('images', {}).get('edges', [])
        if images:
            image_url = images[0].get('node', {}).get('url')
    
    if not image_url:
        print("\n❌ No product image found")
        return
    
    print(f"\n🖼️  Image URL: {image_url}")
    
    # Download and process image
    print("\n🎨 Extracting colors...")
    image = download_image(image_url)
    if not image:
        return
    
    # Extract dominant color
    dominant_colors = get_dominant_color(image, num_colors=1)
    if not dominant_colors:
        print("❌ Failed to extract dominant color")
        return
    
    dominant_color = dominant_colors[0]['hex']
    print(f"\n✨ NEW COLORS:")
    print(f"   Dominant: {dominant_color}")
    
    # Generate complementary color (simple opposite hue)
    complementary_color = get_complementary_color(dominant_color)
    dom_comp_contrast = get_contrast_ratio(dominant_color, complementary_color)
    print(f"   Complementary: {complementary_color} (contrast with dominant: {dom_comp_contrast:.2f}:1)")
    
    # Generate text color based on contrast requirements
    text_color = generate_text_color_from_dominant(dominant_color, complementary_color)
    comp_text_contrast = get_contrast_ratio(complementary_color, text_color)
    dom_text_contrast = get_contrast_ratio(dominant_color, text_color)
    
    # Show text color generation method
    if text_color == dominant_color:
        print(f"   Text: {text_color} (using dominant color - already has good contrast)")
    else:
        print(f"   Text: {text_color} (generated random color closest to 4.5:1 contrast)")
    
    # Show all contrast ratios
    print(f"\n📊 CONTRAST RATIOS:")
    print(f"   Dominant ↔ Text: {dom_text_contrast:.2f}:1")
    print(f"   Dominant ↔ Complementary: {dom_comp_contrast:.2f}:1 {'✓' if dom_comp_contrast >= 3.0 else '✗'}")
    print(f"   Complementary ↔ Text: {comp_text_contrast:.2f}:1 {'✓' if comp_text_contrast >= 4.5 else '✗'}")
    
    # Compare with existing colors if they exist
    if color_fields:
        print(f"\n🔄 COMPARISON WITH EXISTING:")
        if 'dominant_color' in color_fields:
            print(f"   Dominant: {color_fields['dominant_color']} → {dominant_color}")
        if 'complementary_color' in color_fields and 'text_color' in color_fields:
            old_contrast = get_contrast_ratio(color_fields['complementary_color'], color_fields['text_color'])
            print(f"   Old Comp↔Text contrast: {old_contrast:.2f}:1")
            print(f"   New Comp↔Text contrast: {comp_text_contrast:.2f}:1")
            if comp_text_contrast > old_contrast:
                print(f"   ✨ Improvement: +{comp_text_contrast - old_contrast:.2f}")
    
    # Ask for confirmation to save
    print("\n" + "=" * 60)
    confirm = input("\n💾 Save these colors to the product? (y/n): ").strip().lower()
    
    if confirm == 'y':
        print("\n📤 Updating metafields...")
        if update_product_colors(product.get('id'), dominant_color, complementary_color, text_color):
            print("✅ Colors successfully saved!")
            print(f"   • dominant_color: {dominant_color}")
            print(f"   • complementary_color: {complementary_color}")
            print(f"   • text_color: {text_color}")
        else:
            print("❌ Failed to save colors")
    else:
        print("❌ Update cancelled")
    
    print("\n" + "=" * 60)

def main():
    """Main function."""
    if len(sys.argv) > 1:
        # Use command line argument
        product_id = sys.argv[1]
    else:
        # Ask for input
        product_id = input("Enter product ID or handle: ").strip()
    
    if not product_id:
        print("❌ No product ID provided")
        return
    
    process_product(product_id)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Process interrupted by user.")
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc() 