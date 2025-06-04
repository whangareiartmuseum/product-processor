import requests
import json
import time
from tqdm import tqdm

# Shopify API Configuration
SHOP_URL = "your-store.myshopify.com"
ACCESS_TOKEN = "REDACTED_SHOPIFY_TOKEN"
GRAPHQL_URL = f"https://{SHOP_URL}/admin/api/2024-01/graphql.json"

def get_all_products(cursor=None, products=None):
    """
    Get all products from the store with metafield data.
    """
    if products is None:
        products = []
        
    headers = {
        'X-Shopify-Access-Token': ACCESS_TOKEN,
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
    
    variables = {}
    if cursor:
        variables["cursor"] = cursor
    
    payload = {
        "query": query,
        "variables": variables
    }
    
    response = requests.post(GRAPHQL_URL, headers=headers, json=payload)
    
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
        return get_all_products(cursor=end_cursor, products=products)
    
    return products

def clear_unwanted_metafields(product):
    """
    Clear unwanted metafields by setting them to empty/null values.
    """
    product_title = product.get('title', 'Unknown')
    product_id = product.get('id')
    metafields = product.get('metafields', {}).get('edges', [])
    
    # Define what we want to keep
    keep_metafields = {
        ('wam_color_manager', 'dominant_color'),
        ('wam_color_manager', 'complementary_color'),
        ('wam_color_manager', 'text_color'),
    }
    
    # Find metafields to clear
    to_clear = []
    
    for mf_edge in metafields:
        mf = mf_edge.get('node', {})
        namespace = mf.get('namespace', '')
        key = mf.get('key', '')
        value = mf.get('value', '')
        mf_type = mf.get('type', 'single_line_text_field')
        
        # Clear if it's a color field we don't want
        should_clear = False
        
        # Custom namespace color fields
        if namespace == 'custom' and key in ['dominant_colour', 'complementary_colour', 'text_colour', 
                                             'dominant_color', 'complementary_color', 'text_color']:
            should_clear = True
            
        # Wrong wam_color_manager fields (like "colors")
        elif namespace == 'wam_color_manager' and (namespace, key) not in keep_metafields:
            should_clear = True
            
        if should_clear and value:  # Only clear if it has a value
            to_clear.append({
                'namespace': namespace,
                'key': key,
                'type': mf_type,
                'current_value': value[:50]  # First 50 chars
            })
    
    if not to_clear:
        return 0
    
    print(f"\n📦 {product_title}")
    print(f"   Found {len(to_clear)} metafield(s) to clear:")
    for mf in to_clear:
        print(f"   - {mf['namespace']}.{mf['key']} = {mf['current_value']}")
    
    # Clear them by updating to empty values
    headers = {
        'X-Shopify-Access-Token': ACCESS_TOKEN,
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
    
    # Create metafield inputs with empty values
    metafield_inputs = []
    for mf in to_clear:
        # Use appropriate empty value based on type
        empty_value = ""
        if mf['type'] == 'json':
            empty_value = "{}"
        elif mf['type'] == 'boolean':
            empty_value = "false"
        elif mf['type'] == 'number_integer' or mf['type'] == 'number_decimal':
            empty_value = "0"
            
        metafield_inputs.append({
            "namespace": mf['namespace'],
            "key": mf['key'],
            "value": empty_value,
            "type": mf['type']
        })
    
    variables = {
        "productId": product_id,
        "metafields": metafield_inputs
    }
    
    payload = {
        "query": mutation,
        "variables": variables
    }
    
    try:
        response = requests.post(GRAPHQL_URL, headers=headers, json=payload)
        
        if response.status_code != 200:
            print(f"   ❌ HTTP Error {response.status_code}")
            return 0
        
        data = response.json()
        
        if 'errors' in data:
            print(f"   ❌ GraphQL error: {data['errors'][0]['message']}")
            return 0
        
        user_errors = data.get('data', {}).get('productUpdate', {}).get('userErrors', [])
        if user_errors:
            print(f"   ❌ User error: {user_errors[0]['message']}")
            return 0
        
        print(f"   ✅ Cleared {len(to_clear)} metafield(s)")
        return len(to_clear)
        
    except Exception as e:
        print(f"   ❌ Exception: {str(e)}")
        return 0

def main():
    """
    Main cleanup function.
    """
    print("\n🧹 Metafield Clear Script")
    print("=" * 60)
    print("\nThis script will CLEAR (empty) unwanted color metafields, keeping only:")
    print("  • wam_color_manager.dominant_color")
    print("  • wam_color_manager.complementary_color")
    print("  • wam_color_manager.text_color")
    print("\nIt will CLEAR (set to empty):")
    print("  • Any color fields in 'custom' namespace")
    print("  • Any other fields in 'wam_color_manager' namespace (like 'colors')")
    
    confirm = input("\nAre you sure you want to proceed? (yes/no): ").strip().lower()
    if confirm != 'yes':
        print("Cancelled.")
        return
    
    # Fetch all products
    print("\nFetching all products...")
    all_products = get_all_products()
    print(f"✅ Found {len(all_products)} products")
    
    # Process each product
    total_cleared = 0
    products_cleared = 0
    
    print("\nClearing metafields...")
    for product in tqdm(all_products, desc="Processing products"):
        cleared = clear_unwanted_metafields(product)
        if cleared > 0:
            products_cleared += 1
            total_cleared += cleared
        
        # Rate limiting
        time.sleep(0.3)
    
    # Summary
    print("\n" + "=" * 60)
    print("🎉 CLEANUP COMPLETE")
    print("=" * 60)
    print(f"📊 Products processed: {len(all_products)}")
    print(f"🧹 Products cleared: {products_cleared}")
    print(f"📝 Total metafields cleared: {total_cleared}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Process interrupted by user.")
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc() 