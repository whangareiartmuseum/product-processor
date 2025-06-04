import requests
import json

# Shopify API Configuration
SHOP_URL = "your-store.myshopify.com"
ACCESS_TOKEN = "REDACTED_SHOPIFY_TOKEN"
GRAPHQL_URL = f"https://{SHOP_URL}/admin/api/2024-01/graphql.json"

def inspect_colors_field():
    """
    Inspect the wam_color_manager.colors field to understand its structure.
    """
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
    
    payload = {
        "query": query
    }
    
    response = requests.post(GRAPHQL_URL, headers=headers, json=payload)
    
    if response.status_code != 200:
        print(f"Failed to get products: {response.status_code}")
        return
    
    data = response.json()
    products = data.get('data', {}).get('products', {}).get('edges', [])
    
    print("\n🔍 Inspecting Metafield Structure")
    print("=" * 80)
    
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
            print(f"\n📦 {title}")
            for mf in color_fields:
                namespace = mf.get('namespace', '')
                key = mf.get('key', '')
                value = mf.get('value', '')
                mf_type = mf.get('type', '')
                mf_id = mf.get('id', '')
                
                print(f"\n   • {namespace}.{key}")
                print(f"     Type: {mf_type}")
                print(f"     ID: {mf_id}")
                
                # If it's JSON, try to parse and pretty print
                if mf_type == 'json' and value:
                    try:
                        parsed = json.loads(value)
                        print(f"     Value (parsed JSON):")
                        print(f"     {json.dumps(parsed, indent=6)}")
                    except:
                        print(f"     Value: {value[:200]}...")
                else:
                    print(f"     Value: {value[:200] if len(value) > 200 else value}")

def main():
    inspect_colors_field()

if __name__ == "__main__":
    main() 