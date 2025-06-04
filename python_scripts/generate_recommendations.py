import requests
import json
import time
import os
import numpy as np
from openai import OpenAI
from tqdm import tqdm
import re
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('product_recommendations.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Shopify API Configuration from environment variables
SHOP_URL = os.environ.get('SHOPIFY_SHOP_URL')
ACCESS_TOKEN = os.environ.get('SHOPIFY_ACCESS_TOKEN', '')
if not SHOP_URL:
    logger.error("SHOPIFY_SHOP_URL environment variable is not set")
    raise ValueError("SHOPIFY_SHOP_URL is required")
if not ACCESS_TOKEN:
    logger.error("SHOPIFY_ACCESS_TOKEN environment variable is not set")
    raise ValueError("SHOPIFY_ACCESS_TOKEN is required")
GRAPHQL_URL = f"https://{SHOP_URL}/admin/api/2024-01/graphql.json"

# OpenAI Configuration from environment variable
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
if not OPENAI_API_KEY:
    logger.error("OPENAI_API_KEY environment variable is not set")
    raise ValueError("OPENAI_API_KEY is required")

client = OpenAI(api_key=OPENAI_API_KEY)

# Configuration options
MAX_RELATED_PRODUCTS = 10  # Maximum number of related products to suggest per product
CANDIDATE_POOL_SIZE = 15  # Number of candidates to consider from embedding similarity
EMBEDDING_BATCH_SIZE = 20  # Batch size for embedding generation
GPT_BATCH_SIZE = 1  # Process one product at a time with GPT-4o for detailed analysis
START_FROM_PRODUCT = 1  # Start processing from this product number (1-indexed)
MIN_SIMILARITY_THRESHOLD = 0.3  # Minimum cosine similarity to consider a product as candidate
AVOID_SAME_VENDOR = False  # Whether to avoid recommending books from the same vendor/publisher
PRIORITIZE_SAME_COLLECTION = True  # Whether to prioritize books from the same collection

# JSON Schema for related_products metafield
RELATED_PRODUCTS_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "required": ["id", "title", "handle", "url", "reason"],
        "properties": {
            "id": {
                "type": "string",
                "description": "Shopify GraphQL ID of the related product"
            },
            "title": {
                "type": "string",
                "description": "Title of the related product"
            },
            "handle": {
                "type": "string",
                "description": "URL handle of the related product"
            },
            "url": {
                "type": "string",
                "description": "Full URL to the related product"
            },
            "reason": {
                "type": "string",
                "description": "One-sentence explanation why this specific product is related"
            }
        }
    }
}

def get_all_products(cursor=None, products=None):
    """
    Get all products from the store with their descriptions using pagination.
    """
    if products is None:
        products = []
        
    headers = {
        'X-Shopify-Access-Token': ACCESS_TOKEN,
        'Content-Type': 'application/json'
    }
    
    # Query to get products with pagination - including descriptions
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
                    description
                    descriptionHtml
                    handle
                    onlineStoreUrl
                    tags
                    productType
                    vendor
                    totalInventory
                    collections(first: 5) {
                        edges {
                            node {
                                title
                            }
                        }
                    }
                    featuredImage {
                        url
                    }
                    priceRange {
                        minVariantPrice {
                            amount
                            currencyCode
                        }
                    }
                    metafields(first: 10, namespace: "custom") {
                        edges {
                            node {
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
        print(f"Response: {response.text}")
        return products
    
    data = response.json()
    
    if 'errors' in data:
        print(f"GraphQL errors: {json.dumps(data['errors'], indent=2)}")
        return products
    
    product_edges = data.get('data', {}).get('products', {}).get('edges', [])
    products.extend([edge['node'] for edge in product_edges])
    
    # Check if there are more pages
    page_info = data.get('data', {}).get('products', {}).get('pageInfo', {})
    has_next_page = page_info.get('hasNextPage', False)
    
    if has_next_page:
        end_cursor = page_info.get('endCursor')
        # Slight delay to avoid rate limiting
        time.sleep(0.5)
        return get_all_products(cursor=end_cursor, products=products)
    
    return products

def clean_product_data(products):
    """
    Clean and prepare product data for analysis.
    """
    cleaned_products = []
    for product in products:
        # Extract plain text from HTML description if regular description is empty
        description = product.get('description', '')
        if not description and product.get('descriptionHtml'):
            # Simple HTML tag removal - for more complex needs, consider using BeautifulSoup
            import re
            description = re.sub(r'<[^>]+>', '', product.get('descriptionHtml', ''))
        
        # Extract collections
        collections = []
        collection_edges = product.get('collections', {}).get('edges', [])
        for edge in collection_edges:
            collection = edge.get('node', {})
            if collection.get('title'):
                collections.append(collection['title'])
        
        # Extract price
        price_range = product.get('priceRange', {})
        min_price = price_range.get('minVariantPrice', {})
        price = min_price.get('amount', '')
        currency = min_price.get('currencyCode', '')
        
        # Extract custom metafields
        custom_fields = {}
        metafield_edges = product.get('metafields', {}).get('edges', [])
        for edge in metafield_edges:
            metafield = edge.get('node', {})
            key = metafield.get('key', '')
            value = metafield.get('value', '')
            if key and value:
                custom_fields[key] = value
        
        # Create a clean product object with all the data we need
        cleaned_product = {
            'id': product.get('id'),
            'title': product.get('title', ''),
            'description': description,
            'handle': product.get('handle', ''),
            'url': product.get('onlineStoreUrl', ''),
            'tags': product.get('tags', []),
            'productType': product.get('productType', ''),
            'vendor': product.get('vendor', ''),
            'collections': collections,
            'price': price,
            'currency': currency,
            'custom_fields': custom_fields,
            'totalInventory': product.get('totalInventory', 0)
        }
        cleaned_products.append(cleaned_product)
    
    return cleaned_products

def get_embeddings_batch(texts, model="text-embedding-3-small"):
    """
    Get embeddings for a batch of texts.
    
    Args:
        texts: List of text strings to embed
        model: Embedding model to use
        
    Returns:
        list: List of embedding vectors
    """
    try:
        response = client.embeddings.create(
            model=model,
            input=texts
        )
        
        # Extract embeddings from response
        embeddings = [item.embedding for item in response.data]
        return embeddings
    
    except Exception as e:
        print(f"Error getting embeddings: {str(e)}")
        return None

def create_product_embeddings(products):
    """
    Create embeddings for all products in batches.
    
    Args:
        products: List of product dictionaries
        
    Returns:
        dict: Dictionary mapping product IDs to embeddings
    """
    print("Generating embeddings for all products...")
    
    # Prepare texts for embedding
    texts = []
    product_ids = []
    
    for product in products:
        # Build comprehensive text representation for better embeddings
        text_parts = [
            f"Title: {product['title']}",
            f"Description: {product['description']}"
        ]
        
        # Add product type and vendor if available
        if product.get('productType'):
            text_parts.append(f"Type: {product['productType']}")
        if product.get('vendor'):
            text_parts.append(f"Author/Publisher: {product['vendor']}")
        
        # Add tags if available
        if product.get('tags'):
            text_parts.append(f"Tags: {', '.join(product['tags'])}")
        
        # Add collections
        if product.get('collections'):
            text_parts.append(f"Collections: {', '.join(product['collections'])}")
        
        # Add key custom fields that might be relevant (like genre, subject, etc.)
        custom_fields = product.get('custom_fields', {})
        for key, value in custom_fields.items():
            if key.lower() in ['genre', 'subject', 'category', 'author', 'artist', 'period', 'style']:
                text_parts.append(f"{key}: {value}")
        
        text = '\n'.join(text_parts)
        texts.append(text)
        product_ids.append(product['id'])
    
    # Process in batches to avoid API limits
    embeddings_map = {}
    
    for i in tqdm(range(0, len(texts), EMBEDDING_BATCH_SIZE), desc="Embedding Batches"):
        batch_texts = texts[i:i + EMBEDDING_BATCH_SIZE]
        batch_ids = product_ids[i:i + EMBEDDING_BATCH_SIZE]
        
        embeddings = get_embeddings_batch(batch_texts)
        
        if embeddings:
            for j, product_id in enumerate(batch_ids):
                embeddings_map[product_id] = embeddings[j]
        
        # Avoid rate limiting
        if i + EMBEDDING_BATCH_SIZE < len(texts):
            time.sleep(0.5)
    
    return embeddings_map

def find_similar_products(products, embeddings_map, products_map, n=CANDIDATE_POOL_SIZE):
    """
    Find similar products for each product based on embedding similarity.
    
    Args:
        products: List of product dictionaries
        embeddings_map: Dictionary mapping product IDs to embeddings
        products_map: Dictionary mapping product IDs to product data
        n: Number of similar products to find
        
    Returns:
        dict: Dictionary mapping product IDs to lists of similar product IDs
    """
    print("Finding similar products based on embedding similarity...")
    
    # Convert embeddings to numpy arrays for faster processing
    product_ids = list(embeddings_map.keys())
    embedding_matrix = np.array([embeddings_map[pid] for pid in product_ids])
    
    # Normalize embeddings for cosine similarity
    norms = np.linalg.norm(embedding_matrix, axis=1, keepdims=True)
    normalized_embeddings = embedding_matrix / norms
    
    # Calculate cosine similarity matrix
    similarity_matrix = np.dot(normalized_embeddings, normalized_embeddings.T)
    
    # Find top n similar products for each product
    similar_products = {}
    
    for i, product_id in enumerate(tqdm(product_ids, desc="Finding Similar Products")):
        current_product = products_map.get(product_id, {})
        
        # Get similarity scores for current product
        similarities = similarity_matrix[i]
        
        # Create list of (index, similarity) tuples
        similarity_pairs = [(idx, sim) for idx, sim in enumerate(similarities)]
        
        # Filter based on minimum similarity threshold
        similarity_pairs = [(idx, sim) for idx, sim in similarity_pairs 
                          if sim >= MIN_SIMILARITY_THRESHOLD and idx != i]
        
        # Apply vendor filter if configured
        if AVOID_SAME_VENDOR and current_product.get('vendor'):
            current_vendor = current_product['vendor']
            filtered_pairs = []
            for idx, sim in similarity_pairs:
                candidate_id = product_ids[idx]
                candidate = products_map.get(candidate_id, {})
                if candidate.get('vendor') != current_vendor:
                    filtered_pairs.append((idx, sim))
            similarity_pairs = filtered_pairs
        
        # Filter out likely duplicates
        filtered_pairs = []
        for idx, sim in similarity_pairs:
            candidate_id = product_ids[idx]
            candidate = products_map.get(candidate_id, {})
            
            # Check if this is likely a duplicate
            if not is_likely_duplicate(current_product, candidate, sim):
                filtered_pairs.append((idx, sim))
            else:
                print(f"  Skipping likely duplicate: {candidate.get('title', 'Unknown')}")
        
        similarity_pairs = filtered_pairs
        
        # Filter out out-of-stock products
        in_stock_pairs = []
        for idx, sim in similarity_pairs:
            candidate_id = product_ids[idx]
            candidate = products_map.get(candidate_id, {})
            
            # Check if product is in stock (totalInventory > 0)
            if candidate.get('totalInventory', 0) > 0:
                in_stock_pairs.append((idx, sim))
            else:
                print(f"  Skipping out-of-stock product: {candidate.get('title', 'Unknown')}")
        
        similarity_pairs = in_stock_pairs
        
        # Prioritize same collection if configured
        if PRIORITIZE_SAME_COLLECTION and current_product.get('collections'):
            current_collections = set(current_product['collections'])
            
            # Separate into same collection and different collection
            same_collection = []
            diff_collection = []
            
            for idx, sim in similarity_pairs:
                candidate_id = product_ids[idx]
                candidate = products_map.get(candidate_id, {})
                candidate_collections = set(candidate.get('collections', []))
                
                if current_collections & candidate_collections:  # Has overlap
                    same_collection.append((idx, sim))
                else:
                    diff_collection.append((idx, sim))
            
            # Sort each group by similarity
            same_collection.sort(key=lambda x: x[1], reverse=True)
            diff_collection.sort(key=lambda x: x[1], reverse=True)
            
            # Combine, prioritizing same collection
            similarity_pairs = same_collection + diff_collection
        else:
            # Sort by similarity score (descending)
            similarity_pairs.sort(key=lambda x: x[1], reverse=True)
        
        # Take top n candidates
        top_indices = [idx for idx, _ in similarity_pairs[:n]]
        
        # Map indices back to product IDs
        similar_ids = [product_ids[idx] for idx in top_indices]
        similar_products[product_id] = similar_ids
    
    return similar_products

def generate_related_products_explanation(product, candidates, all_products_map):
    """
    Use GPT-4o to select and explain related products from candidates.
    
    Args:
        product: The main product
        candidates: List of candidate related product IDs
        all_products_map: Dictionary mapping product IDs to product data
        
    Returns:
        dict: Dictionary with related products data and explanations
    """
    # Build comprehensive product information
    def format_product_info(prod):
        info_parts = [
            f"Title: {prod['title']}",
            f"Description: {prod['description']}"
        ]
        
        if prod.get('vendor'):
            info_parts.append(f"Author/Publisher: {prod['vendor']}")
        if prod.get('productType'):
            info_parts.append(f"Type: {prod['productType']}")
        if prod.get('tags'):
            info_parts.append(f"Tags: {', '.join(prod['tags'])}")
        if prod.get('collections'):
            info_parts.append(f"Collections: {', '.join(prod['collections'])}")
        if prod.get('price') and prod.get('currency'):
            info_parts.append(f"Price: {prod['currency']} {prod['price']}")
        
        # Add stock status
        inventory = prod.get('totalInventory', 0)
        if inventory > 0:
            info_parts.append(f"Stock Status: In Stock ({inventory} available)")
        else:
            info_parts.append("Stock Status: Out of Stock")
        
        # Add relevant custom fields
        custom_fields = prod.get('custom_fields', {})
        for key, value in custom_fields.items():
            if key.lower() in ['genre', 'subject', 'category', 'author', 'artist', 'period', 'style', 'isbn']:
                info_parts.append(f"{key.title()}: {value}")
        
        return '\n'.join(info_parts)
    
    # Build candidate information
    candidate_info = []
    for i, candidate_id in enumerate(candidates):
        candidate = all_products_map.get(candidate_id)
        if candidate:
            candidate_info.append(f"Candidate {i+1}:\n{format_product_info(candidate)}\n")
    
    candidates_text = "\n".join(candidate_info)
    
    prompt = f"""
You are a friendly bookstore guide helping customers find great related books. Keep your recommendations simple and easy to understand.

MAIN BOOK:
{format_product_info(product)}

CANDIDATE RELATED BOOKS:
{candidates_text}

Your task:
1. Select the top {MAX_RELATED_PRODUCTS} most related books from the candidates
2. Think about connections like:
   - Similar topics or themes
   - Same artists or time periods
   - Books that go well together
   - Similar price range
3. Write a simple category reason (one short sentence about what connects these books)
4. For each book, write a brief reason why it's related (keep it simple and under 15 words)

Make your language friendly and accessible - imagine explaining to a curious museum visitor.

Format your response as a JSON object with:
- "category_reason": brief explanation of what connects these books
- "selected_books": array of objects, each with:
  - "candidate_number": the number of the selected candidate
  - "reason": short, simple explanation of why this book is related

Example format:
{{
  "category_reason": "More books about Dutch art and artists",
  "selected_books": [
    {{
      "candidate_number": 3,
      "reason": "Shows the same artist's later paintings"
    }},
    {{
      "candidate_number": 7,
      "reason": "Explores the art movement that inspired this painter"
    }}
  ]
}}

Only include the JSON in your response, no other text.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",  # Using OpenAI's most advanced model for higher quality recommendations
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You are a friendly museum bookstore assistant who helps visitors find books they'll love. Use simple, clear language that anyone can understand. Keep explanations brief and engaging."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3  # Slightly increased for more creative connections
        )
        
        # Extract the JSON response
        result = json.loads(response.choices[0].message.content)
        
        # Process the response
        category_reason = result.get("category_reason", "Related books you might enjoy")
        selected_books = result.get("selected_books", [])
        
        # Map the selected candidates to actual product IDs and reasons
        related_ids = []
        specific_reasons = {}
        
        for book in selected_books:
            candidate_number = book.get("candidate_number")
            reason = book.get("reason", "Related to your current selection")
            
            if candidate_number and 1 <= candidate_number <= len(candidates):
                related_id = candidates[candidate_number - 1]
                related_ids.append(related_id)
                specific_reasons[related_id] = reason
        
        return {
            "related_ids": related_ids,
            "category_reason": category_reason,
            "specific_reasons": specific_reasons
        }
        
    except Exception as e:
        print(f"Error using OpenAI API: {str(e)}")
        return {
            "related_ids": [],
            "category_reason": "Related books you might enjoy",
            "specific_reasons": {}
        }

def format_related_products_for_metafield(product_id, related_data, all_products_map):
    """
    Format related products data for the metafield.
    
    Args:
        product_id: The product ID
        related_data: Dictionary with related product data including IDs and explanations
        all_products_map: Dictionary mapping product IDs to product data
        
    Returns:
        list: Formatted related products data as an array
    """
    related_ids = related_data.get("related_ids", [])
    category_reason = related_data.get("category_reason", "Related books you might enjoy")
    
    # Store the category reason in the first item as a special entry
    products_list = [{
        "id": "category",
        "reason": category_reason
    }]
    
    # Add only the product IDs for related products
    for related_id in related_ids:
        # Extract just the numeric ID from the GID format
        numeric_id = related_id.split('/')[-1] if '/' in related_id else related_id
        products_list.append({
            "id": numeric_id
        })
    
    # Return a flat array structure
    return products_list

def update_related_products_metafield(product_id, related_products):
    """
    Update the related products metafield for a product.
    
    Args:
        product_id: The GraphQL ID of the product
        related_products: List of related product IDs
        
    Returns:
        bool: Whether the update was successful
    """
    headers = {
        'X-Shopify-Access-Token': ACCESS_TOKEN,
        'Content-Type': 'application/json'
    }
    
    # Prepare the related products as a JSON string
    related_json = json.dumps(related_products)
    
    # Mutation to update product metafield
    mutation = """
    mutation productUpdate($input: ProductInput!) {
        productUpdate(input: $input) {
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
        "input": {
            "id": product_id,
            "metafields": [
                {
                    "namespace": "wam_product_recommendations",
                    "key": "related_products",
                    "value": related_json,
                    "type": "json"
                }
            ]
        }
    }
    
    payload = {
        "query": mutation,
        "variables": variables
    }
    
    response = requests.post(GRAPHQL_URL, headers=headers, json=payload)
    
    if response.status_code != 200:
        print(f"Failed to update related products metafield: {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    data = response.json()
    
    if 'errors' in data:
        print(f"GraphQL errors: {json.dumps(data['errors'], indent=2)}")
        return False
    
    user_errors = data.get('data', {}).get('productUpdate', {}).get('userErrors', [])
    if user_errors:
        print(f"User errors: {json.dumps(user_errors, indent=2)}")
        return False
    
    return True

def is_likely_duplicate(product1, product2, similarity_score):
    """
    Check if two products are likely duplicates or too similar (e.g., different editions).
    
    Args:
        product1: First product dictionary
        product2: Second product dictionary
        similarity_score: Cosine similarity between the products
        
    Returns:
        bool: True if products are likely duplicates
    """
    # Very high similarity could indicate duplicate
    if similarity_score > 0.95:
        return True
    
    # Check if titles are very similar (could be different editions)
    title1 = product1.get('title', '').lower()
    title2 = product2.get('title', '').lower()
    
    # Remove common edition words
    edition_words = ['paperback', 'hardcover', 'kindle', 'ebook', 'edition', 'revised', 'updated', '2nd', '3rd']
    for word in edition_words:
        title1 = title1.replace(word, '')
        title2 = title2.replace(word, '')
    
    # Calculate title similarity
    title1_words = set(title1.split())
    title2_words = set(title2.split())
    
    if len(title1_words) > 0 and len(title2_words) > 0:
        overlap = len(title1_words & title2_words)
        total = len(title1_words | title2_words)
        title_similarity = overlap / total
        
        # If titles are very similar and embeddings are similar, likely duplicate
        if title_similarity > 0.8 and similarity_score > 0.85:
            return True
    
    return False

def main():
    """Main function to process all products and update related products."""
    try:
        print("Starting the Shopify related products generator using embeddings + GPT-4o...")
        print(f"Will suggest up to {MAX_RELATED_PRODUCTS} related products per product.")
        print("Note: Out-of-stock products will be excluded from recommendations.")
        
        # Get all products with descriptions
        print("Fetching all products with descriptions...")
        all_products = get_all_products()
        total_products = len(all_products)
        
        if total_products == 0:
            print("No products found. Exiting.")
            return
        
        print(f"Found {total_products} products to process.")
        
        # Clean product data
        print("Cleaning product data...")
        cleaned_products = clean_product_data(all_products)
        
        # Create a map for easy lookup
        products_map = {p['id']: p for p in cleaned_products}
        
        # Generate embeddings for all products
        embeddings_map = create_product_embeddings(cleaned_products)
        
        # Find similar products based on embeddings
        similar_products_map = find_similar_products(cleaned_products, embeddings_map, products_map)
        
        # Process each product with GPT-4o to generate explanations
        print("\nGenerating detailed recommendations with GPT-4o...")
        related_products_map = {}
        
        # Start from the specified product number
        start_index = START_FROM_PRODUCT - 1  # Convert to 0-indexed
        if start_index >= total_products:
            print(f"START_FROM_PRODUCT ({START_FROM_PRODUCT}) is greater than total products ({total_products})")
            return
        
        products_to_process = cleaned_products[start_index:]
        print(f"Starting from product {START_FROM_PRODUCT} ({total_products - start_index} products remaining)")
        
        for i, product in enumerate(tqdm(products_to_process, desc="Processing Products")):
            actual_index = start_index + i + 1  # Actual product number (1-indexed)
            product_id = product['id']
            print(f"\nProcessing {actual_index}/{total_products}: {product['title']} ({product_id})")
            
            # Get candidate related products
            candidates = similar_products_map.get(product_id, [])
            
            if not candidates:
                print(f"No similar products found for {product['title']}")
                continue
            
            # Generate explanations with GPT-4o
            related_data = generate_related_products_explanation(product, candidates, products_map)
            related_products_map[product_id] = related_data
            
            # Format and update the metafield
            formatted_data = format_related_products_for_metafield(product_id, related_data, products_map)
            
            # Update the metafield
            if update_related_products_metafield(product_id, formatted_data):
                num_related = len(formatted_data) - 1  # Subtract 1 for the category reason entry
                print(f"✅ Successfully updated with {num_related} related products")
            else:
                print(f"❌ Failed to update related products")
            
            # Slight delay to avoid rate limiting
            time.sleep(0.5)
        
        # Print summary
        success_count = sum(1 for p_id in related_products_map if related_products_map[p_id].get('related_ids'))
        print("\n===== SUMMARY =====")
        print(f"Total products processed: {total_products}")
        print(f"Successfully generated recommendations: {success_count}")
        print(f"Failed recommendations: {total_products - success_count}")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 