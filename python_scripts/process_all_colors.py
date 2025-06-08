import requests
import json
import time
import argparse
from PIL import Image
from io import BytesIO
from color_extractor_fixed import get_dominant_color, get_complementary_color, generate_text_color_with_contrast, get_contrast_ratio, generate_text_color_from_dominant
import os

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
    """
    Get all products from the store with image data and color metafields.
    """
    if products is None:
        products = []
        
    # Get config values
    shop_url, access_token, graphql_url = get_shopify_config()
        
    headers = {
        'X-Shopify-Access-Token': access_token,
        'Content-Type': 'application/json'
    }
    
    # Query to get products with images and metafields
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
                    status
                    featuredImage {
                        id
                        url
                    }
                    images(first: 5) {
                        edges {
                            node {
                                id
                                url
                            }
                        }
                    }
                    metafields(first: 30) {
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
    
    response = requests.post(graphql_url, headers=headers, json=payload)
    
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
        time.sleep(0.5)  # Rate limiting
        return get_all_products_with_colors(cursor=end_cursor, products=products)
    
    return products

def get_single_product(product_id):
    """
    Get a single product by ID.
    """
    # Get config values
    shop_url, access_token, graphql_url = get_shopify_config()
    
    headers = {
        'X-Shopify-Access-Token': access_token,
        'Content-Type': 'application/json'
    }
    
    query = """
    query GetProduct($id: ID!) {
        product(id: $id) {
            id
            title
            handle
            status
            featuredImage {
                id
                url
            }
            images(first: 5) {
                edges {
                    node {
                        id
                        url
                    }
                }
            }
            metafields(first: 30) {
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
    """
    
    variables = {
        "id": product_id
    }
    
    payload = {
        "query": query,
        "variables": variables
    }
    
    response = requests.post(graphql_url, headers=headers, json=payload)
    
    if response.status_code != 200:
        print(f"Failed to get product: {response.status_code}")
        print(f"Response: {response.text}")
        return None
    
    data = response.json()
    
    if 'errors' in data:
        print(f"GraphQL errors: {json.dumps(data['errors'], indent=2)}")
        return None
    
    return data.get('data', {}).get('product')

def check_color_metafields(product):
    """
    Check which color metafields exist for a product.
    Returns dict with status of each color metafield.
    """
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

def has_empty_color_metafields(product):
    """
    Check if product has any empty color metafields.
    """
    color_status = check_color_metafields(product)
    return not all(status['exists'] for status in color_status.values())

def get_product_image_url(product):
    """
    Get the first available image URL for a product.
    """
    # Try featured image first
    featured_image = product.get('featuredImage')
    if featured_image:
        return featured_image.get('url')
    
    # Otherwise get first image from images list
    images = product.get('images', {}).get('edges', [])
    if images:
        return images[0].get('node', {}).get('url')
    
    return None

def download_image(url):
    """
    Download image from URL and return PIL Image object.
    """
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return Image.open(BytesIO(response.content))
    except Exception as e:
        print(f"Error downloading image: {e}")
    return None

def update_product_color_metafields(product_id, dominant_color, complementary_color, text_color):
    """
    Update all three color metafields for a product.
    """
    # Get config values
    shop_url, access_token, graphql_url = get_shopify_config()
    
    headers = {
        'X-Shopify-Access-Token': access_token,
        'Content-Type': 'application/json'
    }
    
    print(f"\n🔧 Updating metafields for product {product_id}")
    print(f"   Dominant: {dominant_color}")
    print(f"   Complementary: {complementary_color}")
    print(f"   Text: {text_color}")
    
    # Mutation to update product metafields
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
    
    payload = {
        "query": mutation,
        "variables": variables
    }
    
    print("\n📡 Sending GraphQL request...")
    response = requests.post(graphql_url, headers=headers, json=payload)
    
    print(f"Response status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"Failed to update metafields: {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    data = response.json()
    print(f"Response data: {json.dumps(data, indent=2)}")
    
    if 'errors' in data:
        print(f"GraphQL errors: {json.dumps(data['errors'], indent=2)}")
        return False
    
    user_errors = data.get('data', {}).get('productUpdate', {}).get('userErrors', [])
    if user_errors:
        print(f"User errors: {json.dumps(user_errors, indent=2)}")
        return False
    
    # Check if metafields were actually saved
    updated_product = data.get('data', {}).get('productUpdate', {}).get('product', {})
    if updated_product:
        print("\n✅ Updated metafields:")
        metafields = updated_product.get('metafields', {}).get('edges', [])
        for mf in metafields:
            node = mf.get('node', {})
            if node.get('namespace') == 'wam_color_manager' and node.get('key') in ['dominant_color', 'complementary_color', 'text_color']:
                print(f"   {node.get('key')}: {node.get('value')}")
    
    return True

def process_product(product):
    """
    Process a single product and extract/update colors.
    Returns (success, message)
    """
    product_title = product.get('title', 'Unknown')
    product_id = product.get('id')
    
    # Get image URL
    image_url = get_product_image_url(product)
    if not image_url:
        return False, f"No image found for product"
    
    try:
        # Download image
        image = download_image(image_url)
        if not image:
            return False, f"Failed to download image"
        
        # Extract dominant colors
        dominant_colors = get_dominant_color(image, num_colors=1)
        if not dominant_colors:
            return False, f"Failed to extract colors"
        
        # Get the primary dominant color
        dominant_color = dominant_colors[0]['hex']
        
        print(f"\n🔍 Color Generation Debug:")
        print(f"   Dominant color extracted: {dominant_color}")
        
        # Generate complementary color (simple opposite hue)
        complementary_color = get_complementary_color(dominant_color)
        dom_comp_contrast = get_contrast_ratio(dominant_color, complementary_color)
        print(f"   Complementary color generated: {complementary_color}")
        print(f"   Dominant↔Complementary contrast: {dom_comp_contrast:.2f}:1 {'✓' if dom_comp_contrast >= 3.0 else '✗'}")
        
        # Generate text color based on contrast requirements
        text_color = generate_text_color_from_dominant(dominant_color, complementary_color)
        comp_text_contrast = get_contrast_ratio(complementary_color, text_color)
        dom_text_contrast = get_contrast_ratio(dominant_color, text_color)
        
        # Show text color generation method
        if text_color == dominant_color:
            print(f"   Text color: {text_color} (using dominant - already has good contrast)")
        else:
            print(f"   Text color: {text_color} (random color closest to 4.5:1)")
        
        print(f"   Complementary↔Text contrast: {comp_text_contrast:.2f}:1 {'✓' if comp_text_contrast >= 4.5 else '✗'}")
        print(f"   Dominant↔Text contrast: {dom_text_contrast:.2f}:1")
        
        # Update metafields
        if update_product_color_metafields(product_id, dominant_color, complementary_color, text_color):
            return True, f"Updated with colors - Dominant: {dominant_color}, Complementary: {complementary_color}, Text: {text_color}"
        else:
            return False, f"Failed to update metafields"
            
    except Exception as e:
        return False, f"Error: {str(e)}"

def process_all_products():
    """
    Process all products in the store.
    """
    print("\n🎨 Processing ALL products...")
    print("=" * 60)
    
    # Fetch all products
    print("📡 Connecting to Shopify API...")
    print("Fetching all products from Shopify...")
    all_products = get_all_products_with_colors()
    total_products = len(all_products)
    
    if total_products == 0:
        print("No products found.")
        return
    
    print(f"✅ Found {total_products} products total.")
    
    # Filter products with images
    print("\n🔍 Analyzing product images...")
    products_with_images = [p for p in all_products if get_product_image_url(p)]
    products_without_images = total_products - len(products_with_images)
    
    if products_without_images > 0:
        print(f"⚠️  {products_without_images} products have no images and will be skipped.")
    
    print(f"\n🎨 Starting color extraction for {len(products_with_images)} products...")
    print("This process will:")
    print("  1. Download each product image")
    print("  2. Extract dominant color")
    print("  3. Generate complementary color")
    print("  4. Generate text color with proper contrast")
    print("  5. Update product metafields")
    print("\nEstimated time: ~{:.1f} minutes".format(len(products_with_images) * 0.5 / 60))
    print("=" * 60)
    
    successful = 0
    failed = 0
    
    for i, product in enumerate(products_with_images, 1):
        print(f"\n📦 [{i}/{len(products_with_images)}] Processing: {product.get('title', 'Unknown')[:50]}...")
        success, message = process_product(product)
        
        if success:
            successful += 1
            print(f"✅ {message}")
        else:
            failed += 1
            print(f"❌ {message}")
        
        # Progress update every 10 products
        if i % 10 == 0:
            print(f"\n📊 Progress: {i}/{len(products_with_images)} products processed ({i/len(products_with_images)*100:.1f}%)")
            print(f"   Successful: {successful}, Failed: {failed}")
        
        # Rate limiting
        time.sleep(0.5)
    
    print_summary(successful, failed, len(products_with_images))

def process_empty_only():
    """
    Process only products with empty color metafields.
    """
    print("\n🎨 Processing products with EMPTY color metafields...")
    print("=" * 60)
    
    # Fetch all products
    print("📡 Connecting to Shopify API...")
    print("Fetching all products from Shopify...")
    all_products = get_all_products_with_colors()
    
    # Filter products that need updates
    print("\n🔍 Checking which products need color updates...")
    products_to_update = []
    for product in all_products:
        if get_product_image_url(product) and has_empty_color_metafields(product):
            products_to_update.append(product)
    
    print(f"✅ Found {len(products_to_update)} products with missing color data.")
    
    if len(products_to_update) == 0:
        print("✨ All products with images already have complete color data!")
        return
    
    print(f"\n🎨 Starting color extraction for {len(products_to_update)} products...")
    print("This process will update only products missing color metadata.")
    print(f"Estimated time: ~{len(products_to_update) * 0.5 / 60:.1f} minutes")
    print("=" * 60)
    
    successful = 0
    failed = 0
    
    for i, product in enumerate(products_to_update, 1):
        # Show current color status
        color_status = check_color_metafields(product)
        missing = [k for k, v in color_status.items() if not v['exists']]
        print(f"\n📦 [{i}/{len(products_to_update)}] {product.get('title', 'Unknown')[:50]}")
        print(f"   Missing fields: {', '.join(missing)}")
        
        success, message = process_product(product)
        
        if success:
            successful += 1
            print(f"✅ {message}")
        else:
            failed += 1
            print(f"❌ {message}")
        
        # Progress update every 10 products
        if i % 10 == 0:
            print(f"\n📊 Progress: {i}/{len(products_to_update)} products processed ({i/len(products_to_update)*100:.1f}%)")
            print(f"   Successful: {successful}, Failed: {failed}")
        
        # Rate limiting
        time.sleep(0.5)
    
    print_summary(successful, failed, len(products_to_update))

def process_specific_product():
    """
    Process a specific product by ID.
    """
    print("\n🎨 Process SPECIFIC product")
    print("=" * 60)
    
    # Get product ID from user
    product_id = input("\nEnter the product ID (e.g., gid://shopify/Product/1234567890): ").strip()
    
    if not product_id:
        print("❌ No product ID provided.")
        return
    
    # Ensure proper format
    if not product_id.startswith("gid://shopify/Product/"):
        # Try to construct the proper ID format
        if product_id.isdigit():
            product_id = f"gid://shopify/Product/{product_id}"
        else:
            print("❌ Invalid product ID format. Expected format: gid://shopify/Product/1234567890")
            return
    
    print(f"\nFetching product: {product_id}")
    product = get_single_product(product_id)
    
    if not product:
        print("❌ Product not found.")
        return
    
    print(f"✅ Found product: {product.get('title', 'Unknown')}")
    
    # Check current color status
    color_status = check_color_metafields(product)
    print("\n📊 Current color metafields:")
    for field, status in color_status.items():
        if status['exists']:
            print(f"   • {field}: {status['value']}")
        else:
            print(f"   • {field}: [EMPTY]")
    
    # Check for image
    if not get_product_image_url(product):
        print("\n❌ This product has no images. Cannot extract colors.")
        return
    
    # Confirm processing
    confirm = input("\nProcess this product? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Cancelled.")
        return
    
    print("\n🎨 Extracting colors...")
    success, message = process_product(product)
    
    if success:
        print(f"✅ Success! {message}")
    else:
        print(f"❌ Failed: {message}")

def print_summary(successful, failed, total):
    """
    Print processing summary.
    """
    print("\n" + "=" * 60)
    print("🎉 PROCESSING COMPLETE")
    print("=" * 60)
    print(f"✅ Successfully updated: {successful} products")
    print(f"❌ Failed updates: {failed} products")
    print(f"📊 Total processed: {total} products")
    if successful > 0:
        print(f"🎨 Success rate: {(successful/total)*100:.1f}%")

def generate_contrast_report():
    """
    Generate a report on color contrast ratios between complementary and text colors.
    """
    print("\n📊 Generating Color Contrast Report...")
    print("=" * 60)
    
    # Fetch all products
    print("📡 Connecting to Shopify API...")
    print("Fetching all products from Shopify...")
    all_products = get_all_products_with_colors()
    total_products = len(all_products)
    
    if total_products == 0:
        print("No products found.")
        return
    
    print(f"✅ Found {total_products} products total.")
    
    # Analyze products
    report_data = []
    products_with_colors = 0
    products_missing_colors = 0
    
    print("\n🔍 Analyzing color contrast ratios...")
    print("Checking WCAG compliance for text readability...")
    
    for i, product in enumerate(all_products, 1):
        product_title = product.get('title', 'Unknown')
        product_id = product.get('id', '')
        
        # Progress indicator every 50 products
        if i % 50 == 0:
            print(f"📊 Progress: {i}/{total_products} products analyzed ({i/total_products*100:.1f}%)")
        
        # Check color metafields
        color_status = check_color_metafields(product)
        
        # Check if all color fields exist
        if all(status['exists'] for status in color_status.values()):
            products_with_colors += 1
            
            complementary_color = color_status['complementary_color']['value']
            text_color = color_status['text_color']['value']
            dominant_color = color_status['dominant_color']['value']
            
            # Calculate contrast ratio between complementary and text colors
            contrast_ratio = get_contrast_ratio(complementary_color, text_color)
            
            # Determine WCAG compliance
            wcag_aa = contrast_ratio >= 4.5  # AA standard for normal text
            wcag_aaa = contrast_ratio >= 7.0  # AAA standard for normal text
            
            compliance = "AAA" if wcag_aaa else "AA" if wcag_aa else "FAIL"
            
            report_data.append({
                'title': product_title,
                'id': product_id,
                'dominant': dominant_color,
                'complementary': complementary_color,
                'text': text_color,
                'contrast_ratio': contrast_ratio,
                'compliance': compliance
            })
        else:
            products_missing_colors += 1
    
    print(f"\n✅ Analysis complete! Processed {total_products} products.")
    
    # Sort report by contrast ratio (lowest first)
    report_data.sort(key=lambda x: x['contrast_ratio'])
    
    # Generate report
    print("\n" + "=" * 80)
    print("🎨 COLOR CONTRAST REPORT")
    print("=" * 80)
    print(f"\n📊 SUMMARY:")
    print(f"   • Total products: {total_products}")
    print(f"   • Products with complete color data: {products_with_colors}")
    print(f"   • Products missing color data: {products_missing_colors}")
    
    if report_data:
        # Count compliance levels
        aaa_count = sum(1 for item in report_data if item['compliance'] == 'AAA')
        aa_count = sum(1 for item in report_data if item['compliance'] == 'AA')
        fail_count = sum(1 for item in report_data if item['compliance'] == 'FAIL')
        
        print(f"\n🎯 WCAG COMPLIANCE (Complementary vs Text):")
        print(f"   • AAA (7:1+): {aaa_count} products ({aaa_count/len(report_data)*100:.1f}%)")
        print(f"   • AA (4.5:1+): {aa_count} products ({aa_count/len(report_data)*100:.1f}%)")
        print(f"   • FAIL (<4.5:1): {fail_count} products ({fail_count/len(report_data)*100:.1f}%)")
        
        # Show products with poor contrast
        poor_contrast = [item for item in report_data if item['compliance'] == 'FAIL']
        if poor_contrast:
            print(f"\n⚠️  PRODUCTS WITH POOR CONTRAST (<4.5:1):")
            for item in poor_contrast[:10]:  # Show max 10
                print(f"   • {item['title'][:50]}")
                print(f"     Ratio: {item['contrast_ratio']:.2f}:1")
                print(f"     Colors: {item['complementary']} (comp) vs {item['text']} (text)")
            
            if len(poor_contrast) > 10:
                print(f"   ... and {len(poor_contrast) - 10} more")
        
        # Show best and worst contrast
        print(f"\n📈 BEST CONTRAST:")
        best = report_data[-1]
        print(f"   • {best['title'][:50]}")
        print(f"     Ratio: {best['contrast_ratio']:.2f}:1 ({best['compliance']})")
        print(f"     Colors: {best['complementary']} (comp) vs {best['text']} (text)")
        
        print(f"\n📉 WORST CONTRAST:")
        worst = report_data[0]
        print(f"   • {worst['title'][:50]}")
        print(f"     Ratio: {worst['contrast_ratio']:.2f}:1 ({worst['compliance']})")
        print(f"     Colors: {worst['complementary']} (comp) vs {worst['text']} (text)")
        
        # Try to save detailed report to file (use /tmp on serverless)
        try:
            # Check if we're in a serverless environment
            if os.environ.get('VERCEL') or os.environ.get('AWS_LAMBDA_FUNCTION_NAME') or not os.access('.', os.W_OK):
                # Use /tmp directory for serverless environments
                report_filename = f"/tmp/color_contrast_report_{time.strftime('%Y%m%d_%H%M%S')}.txt"
            else:
                # Use current directory for local development
        report_filename = f"color_contrast_report_{time.strftime('%Y%m%d_%H%M%S')}.txt"
            
        with open(report_filename, 'w') as f:
            f.write("COLOR CONTRAST REPORT\n")
            f.write("=" * 80 + "\n")
            f.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total products analyzed: {len(report_data)}\n")
            f.write("\n")
            f.write("Product Title | Contrast Ratio | WCAG | Dominant | Complementary | Text\n")
            f.write("-" * 80 + "\n")
            
            for item in report_data:
                f.write(f"{item['title'][:30]:<30} | {item['contrast_ratio']:>6.2f}:1 | {item['compliance']:<4} | ")
                f.write(f"{item['dominant']} | {item['complementary']} | {item['text']}\n")
        
        print(f"\n💾 Detailed report saved to: {report_filename}")
        except Exception as e:
            # If file saving fails, just skip it (not critical for the report)
            print(f"\n📝 Note: Could not save report file (running in read-only environment)")
    
    else:
        print("\n⚠️  No products with complete color data found.")
    
    print("\n" + "=" * 80)

def main():
    """
    Main function with interactive menu.
    """
    print("\n🎨 Shopify Color Extractor & Updater")
    print("=" * 60)
    print("\nThis tool extracts dominant, complementary, and text colors from product images")
    print("and updates the corresponding metafields in Shopify.")
    
    # Skip metafield definition creation - they already exist
    
    while True:
        print("\n📋 OPTIONS:")
        print("1. Run on ALL products")
        print("2. Run only on products with EMPTY color metafields")
        print("3. Run on a SPECIFIC product")
        print("4. Generate Color Contrast Report")
        print("5. Exit")
        
        choice = input("\nSelect an option (1-5): ").strip()
        
        if choice == '1':
            process_all_products()
        elif choice == '2':
            process_empty_only()
        elif choice == '3':
            process_specific_product()
        elif choice == '4':
            generate_contrast_report()
        elif choice == '5':
            print("\n👋 Goodbye!")
            break
        else:
            print("❌ Invalid option. Please select 1-5.")
        
        # Ask if user wants to continue
        if choice in ['1', '2', '3', '4']:
            another = input("\n\nWould you like to perform another operation? (y/n): ").strip().lower()
            if another != 'y':
                print("\n👋 Goodbye!")
                break

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Shopify Color Extractor & Updater')
    parser.add_argument('--all', action='store_true', help='Process all products')
    parser.add_argument('--empty', action='store_true', help='Process only products with empty color metafields')
    parser.add_argument('--report', action='store_true', help='Generate contrast report')
    parser.add_argument('--contrast-type', choices=['dominant', 'text', 'both', 'comp_text'], 
                       default='comp_text', help='Type of contrast report')
    
    args = parser.parse_args()
    
    try:
        # If command line arguments provided, run directly
        if args.report:
            # For now, we only support comp_text contrast type from command line
            generate_contrast_report()
        elif args.all:
            process_all_products()
        elif args.empty:
            process_empty_only()
        else:
            # No arguments, run interactive menu
            main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Process interrupted by user.")
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc() 