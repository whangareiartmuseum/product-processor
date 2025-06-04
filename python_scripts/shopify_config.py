import os

# Get configuration from environment variables
SHOP_URL = os.getenv('SHOPIFY_SHOP_URL', 'your-store.myshopify.com')
ACCESS_TOKEN = os.getenv('SHOPIFY_ACCESS_TOKEN', 'REDACTED_SHOPIFY_TOKEN')
GRAPHQL_URL = f"https://{SHOP_URL}/admin/api/2024-01/graphql.json" 