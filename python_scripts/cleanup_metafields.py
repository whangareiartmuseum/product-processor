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

def delete_metafields(metafield_ids):
    """
    Delete metafields by their IDs.
    """
    if not metafield_ids:
        return True
        
    headers = {
        'X-Shopify-Access-Token': ACCESS_TOKEN,
        'Content-Type': 'application/json'
    }
    
    # Try deleting one at a time if batch fails
    mutation = """
    mutation metafieldDelete($input: MetafieldDeleteInput!) {
        metafieldDelete(input: $input) {
            deletedId
            userErrors {
                field
                message
            }
        }
    }
    """
    
    successful_deletes = 0
    
    for metafield_id in metafield_ids:
        variables = {
            "input": {
                "id": metafield_id
            }
        }
        
        payload = {
            "query": mutation,
            "variables": variables
        }
        
        try:
            response = requests.post(GRAPHQL_URL, headers=headers, json=payload)
            
            if response.status_code != 200:
                print(f"\n   ❌ HTTP Error {response.status_code} for {metafield_id}")
                continue
            
            data = response.json()
            
            if 'errors' in data:
                print(f"\n   ❌ GraphQL error for {metafield_id}: {data['errors'][0]['message']}")
                continue
            
            user_errors = data.get('data', {}).get('metafieldDelete', {}).get('userErrors', [])
            if user_errors:
                print(f"\n   ❌ User error for {metafield_id}: {user_errors[0]['message']}")
                continue
                
            successful_deletes += 1
            
        except Exception as e:
            print(f"\n   ❌ Exception deleting {metafield_id}: {str(e)}")
            continue
    
    return successful_deletes > 0

def cleanup_product_metafields(product):
    """
    Clean up unwanted metafields from a product.
    Returns count of deleted metafields.
    """
    product_title = product.get('title', 'Unknown')
    metafields = product.get('metafields', {}).get('edges', [])
    
    # Define what we want to keep
    keep_metafields = {
        ('wam_color_manager', 'dominant_color'),
        ('wam_color_manager', 'complementary_color'),
        ('wam_color_manager', 'text_color'),
    }
    
    # Find metafields to delete
    to_delete = []
    
    for mf_edge in metafields:
        mf = mf_edge.get('node', {})
        namespace = mf.get('namespace', '')
        key = mf.get('key', '')
        metafield_id = mf.get('id', '')
        
        # Delete if:
        # 1. It's in custom namespace with color-related keys
        # 2. It's in wam_color_manager but not one of our three keys
        # 3. Any other color-related metafield
        
        should_delete = False
        
        # Custom namespace color fields
        if namespace == 'custom' and key in ['dominant_colour', 'complementary_colour', 'text_colour', 
                                             'dominant_color', 'complementary_color', 'text_color']:
            should_delete = True
            
        # Wrong wam_color_manager fields
        elif namespace == 'wam_color_manager' and (namespace, key) not in keep_metafields:
            should_delete = True
            
        if should_delete:
            to_delete.append({
                'id': metafield_id,
                'namespace': namespace,
                'key': key,
                'value': mf.get('value', '')[:50]  # First 50 chars
            })
    
    if to_delete:
        print(f"\n📦 {product_title}")
        print(f"   Found {len(to_delete)} metafield(s) to delete:")
        for mf in to_delete:
            print(f"   - {mf['namespace']}.{mf['key']} = {mf['value']}")
        
        # Delete them
        metafield_ids = [mf['id'] for mf in to_delete]
        if delete_metafields(metafield_ids):
            print(f"   ✅ Deleted {len(to_delete)} metafield(s)")
            return len(to_delete)
        else:
            print(f"   ❌ Failed to delete metafields")
            return 0
    
    return 0

def main():
    """
    Main cleanup function.
    """
    print("\n🧹 Metafield Cleanup Script")
    print("=" * 60)
    print("\nThis script will delete unwanted color metafields, keeping only:")
    print("  • wam_color_manager.dominant_color")
    print("  • wam_color_manager.complementary_color")
    print("  • wam_color_manager.text_color")
    print("\nIt will DELETE:")
    print("  • Any color fields in 'custom' namespace")
    print("  • Any other fields in 'wam_color_manager' namespace")
    
    confirm = input("\nAre you sure you want to proceed? (yes/no): ").strip().lower()
    if confirm != 'yes':
        print("Cancelled.")
        return
    
    # Fetch all products
    print("\nFetching all products...")
    all_products = get_all_products()
    print(f"✅ Found {len(all_products)} products")
    
    # Process each product
    total_deleted = 0
    products_cleaned = 0
    
    print("\nCleaning up metafields...")
    for product in tqdm(all_products, desc="Processing products"):
        deleted = cleanup_product_metafields(product)
        if deleted > 0:
            products_cleaned += 1
            total_deleted += deleted
        
        # Rate limiting
        time.sleep(0.2)
    
    # Summary
    print("\n" + "=" * 60)
    print("🎉 CLEANUP COMPLETE")
    print("=" * 60)
    print(f"📊 Products processed: {len(all_products)}")
    print(f"🧹 Products cleaned: {products_cleaned}")
    print(f"🗑️  Total metafields deleted: {total_deleted}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Process interrupted by user.")
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc() 