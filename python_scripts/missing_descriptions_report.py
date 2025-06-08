#!/usr/bin/env python3
import os
import sys
import json
from datetime import datetime
import time
import requests

# Get configuration from environment variables
SHOPIFY_SHOP_URL = os.environ.get('SHOPIFY_SHOP_URL', 'your-store.myshopify.com')
SHOPIFY_ACCESS_TOKEN = os.environ.get('SHOPIFY_ACCESS_TOKEN', 'REDACTED_SHOPIFY_TOKEN')

def get_all_products_with_descriptions(cursor=None, products=None):
    """
    Get all products from the store with description data.
    """
    if products is None:
        products = []
    
    headers = {
        'X-Shopify-Access-Token': SHOPIFY_ACCESS_TOKEN,
        'Content-Type': 'application/json'
    }
    
    # Query to get products with descriptions
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
                    vendor
                    productType
                    tags
                    createdAt
                    updatedAt
                    status
                    totalInventory
                    description
                    descriptionHtml
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
    
    graphql_url = f"https://{SHOPIFY_SHOP_URL}/admin/api/2024-01/graphql.json"
    response = requests.post(graphql_url, headers=headers, json=payload)
    
    if response.status_code != 200:
        print(f"Failed to get products: {response.status_code}", file=sys.stderr)
        print(f"Response: {response.text}", file=sys.stderr)
        return products
    
    data = response.json()
    
    if 'errors' in data:
        print(f"❌ GraphQL errors: {json.dumps(data['errors'], indent=2)}", file=sys.stderr)
        return products
    
    product_edges = data.get('data', {}).get('products', {}).get('edges', [])
    products.extend([edge['node'] for edge in product_edges])
    
    # Check if there are more pages
    page_info = data.get('data', {}).get('products', {}).get('pageInfo', {})
    has_next_page = page_info.get('hasNextPage', False)
    
    if has_next_page:
        end_cursor = page_info.get('endCursor')
        time.sleep(0.25)  # Rate limiting
        return get_all_products_with_descriptions(cursor=end_cursor, products=products)
    
    return products

def get_products_missing_descriptions():
    """
    Fetch all products and identify those missing descriptions.
    
    Returns:
        dict: Report containing products with missing descriptions
    """
    print("🔍 Fetching all products to check descriptions...", file=sys.stderr)
    
    all_products = []
    missing_description_products = []
    
    # Fetch all products
    products_data = get_all_products_with_descriptions()
    
    for product in products_data:
        product_info = {
            'id': product['id'].split('/')[-1],
            'title': product['title'],
            'handle': product['handle'],
            'vendor': product.get('vendor', ''),
            'product_type': product.get('productType', ''),
            'tags': product.get('tags', []),
            'created_at': product.get('createdAt', ''),
            'updated_at': product.get('updatedAt', ''),
            'status': product.get('status', ''),
            'total_inventory': product.get('totalInventory', 0),
            'description': product.get('description', '').strip(),
            'description_html': product.get('descriptionHtml', '').strip()
        }
        
        all_products.append(product_info)
        
        # Check if description is missing or empty
        if not product_info['description'] and not product_info['description_html']:
            missing_description_products.append(product_info)
    
    # Generate report
    total_products = len(all_products)
    missing_count = len(missing_description_products)
    percentage = (missing_count / total_products * 100) if total_products > 0 else 0
    
    # Sort missing products by created date (newest first)
    missing_description_products.sort(key=lambda x: x['created_at'], reverse=True)
    
    report = {
        'generated_at': datetime.now().isoformat(),
        'summary': {
            'total_products': total_products,
            'missing_descriptions': missing_count,
            'have_descriptions': total_products - missing_count,
            'missing_percentage': round(percentage, 1)
        },
        'products_missing_descriptions': missing_description_products
    }
    
    # Print summary to stderr
    print("\n" + "="*60, file=sys.stderr)
    print("📊 MISSING DESCRIPTIONS REPORT", file=sys.stderr)
    print("="*60, file=sys.stderr)
    print(f"Total products: {total_products}", file=sys.stderr)
    print(f"Missing descriptions: {missing_count} ({percentage:.1f}%)", file=sys.stderr)
    print(f"Have descriptions: {total_products - missing_count} ({100-percentage:.1f}%)", file=sys.stderr)
    
    if missing_count > 0:
        print(f"\n📝 Products missing descriptions:", file=sys.stderr)
        print("-"*60, file=sys.stderr)
        for i, product in enumerate(missing_description_products[:10], 1):
            print(f"{i}. {product['title']}", file=sys.stderr)
            print(f"   ID: {product['id']} | Handle: {product['handle']}", file=sys.stderr)
            print(f"   Type: {product['product_type']} | Vendor: {product['vendor']}", file=sys.stderr)
            print(f"   Created: {product['created_at'][:10] if product['created_at'] else 'Unknown'}", file=sys.stderr)
            print(file=sys.stderr)
        
        if missing_count > 10:
            print(f"... and {missing_count - 10} more products", file=sys.stderr)
    
    return report

def main():
    """Main function to generate missing descriptions report."""
    try:
        report = get_products_missing_descriptions()
        
        # Output report as JSON
        print(json.dumps(report))
        
    except Exception as e:
        print(json.dumps({
            'error': str(e),
            'generated_at': datetime.now().isoformat()
        }))

if __name__ == "__main__":
    main() 