import os

def get_shopify_config():
    """Get Shopify configuration from environment variables."""
    shop_url = os.getenv('SHOPIFY_SHOP_URL')
    access_token = os.getenv('SHOPIFY_ACCESS_TOKEN')
    
    if not shop_url or not access_token:
        raise ValueError("Missing required environment variables: SHOPIFY_SHOP_URL and/or SHOPIFY_ACCESS_TOKEN")
    
    graphql_url = f"https://{shop_url}/admin/api/2024-01/graphql.json"
    return shop_url, access_token, graphql_url 