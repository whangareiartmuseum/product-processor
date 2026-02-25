import os
import json
import time
import logging
import requests
from typing import List, Dict, Any
from openai import OpenAI

# Config
OVERWRITE_EXISTING = True
MAX_CATEGORIES = 5
OPENAI_MODEL = "gpt-4o"
SHOPIFY_API_VERSION = "2024-01"

# Logging (console only; /tmp for serverless if available)
log_handlers = [logging.StreamHandler()]
try:
    log_path = "/tmp/book_categories.log" if os.environ.get("VERCEL") else "book_categories.log"
    log_handlers.append(logging.FileHandler(log_path))
except OSError:
    pass

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=log_handlers
)
logger = logging.getLogger(__name__)


def get_env(name: str) -> str:
    value = os.environ.get(name, "")
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


SHOP_URL = get_env("SHOPIFY_SHOP_URL")
ACCESS_TOKEN = get_env("SHOPIFY_ACCESS_TOKEN")
OPENAI_API_KEY = get_env("OPENAI_API_KEY")
GRAPHQL_URL = f"https://{SHOP_URL}/admin/api/{SHOPIFY_API_VERSION}/graphql.json"
client = OpenAI(api_key=OPENAI_API_KEY)


def fetch_products(cursor: str = None, acc: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    if acc is None:
        acc = []

    query = """
    query GetProducts($cursor: String) {
      products(first: 50, after: $cursor) {
        pageInfo { hasNextPage endCursor }
        edges {
          node {
            id
            title
            handle
            description
            descriptionHtml
            tags
            productType
            vendor
            metafield(namespace: "custom", key: "book_categories") {
              value
            }
          }
        }
      }
    }
    """

    variables = {"cursor": cursor} if cursor else {}
    resp = requests.post(
        GRAPHQL_URL,
        headers={
            "X-Shopify-Access-Token": ACCESS_TOKEN,
            "Content-Type": "application/json",
        },
        json={"query": query, "variables": variables},
    )
    if resp.status_code != 200:
        raise RuntimeError(f"Shopify fetch failed ({resp.status_code}): {resp.text}")

    data = resp.json()
    if "errors" in data:
        raise RuntimeError(f"GraphQL errors: {data['errors']}")

    edges = data.get("data", {}).get("products", {}).get("edges", [])
    acc.extend([edge["node"] for edge in edges])

    page_info = data.get("data", {}).get("products", {}).get("pageInfo", {})
    if page_info.get("hasNextPage"):
        time.sleep(0.2)
        return fetch_products(page_info.get("endCursor"), acc)
    return acc


def clean_text(html_text: str) -> str:
    import re
    return re.sub(r"<[^>]+>", "", html_text or "")


def build_prompt(product: Dict[str, Any]) -> str:
    description = product.get("description") or clean_text(product.get("descriptionHtml", ""))
    tags = ", ".join(product.get("tags", [])) if product.get("tags") else "none"
    vendor = product.get("vendor") or "unknown"
    product_type = product.get("productType") or "unknown"

    return f"""
You are a research assistant that infers precise book/product categories.
Imagine you quickly skim top Google results about this topic to inform the categories.
Provide 3-5 clear categories with a short reason and 2-3 topical search cues.

Return strict JSON with:
{{
  "categories": [
    {{
      "name": "Category name",
      "reason": "Short reason (<120 chars)",
      "search_terms": ["keyword1", "keyword2"],
      "confidence": 0.0-1.0
    }}
  ]
}}

Product:
- Title: {product.get('title', '')}
- Vendor/Author: {vendor}
- Type: {product_type}
- Tags: {tags}
- Description: {description[:1800]}
"""


def generate_categories(product: Dict[str, Any]) -> List[Dict[str, Any]]:
    prompt = build_prompt(product)
    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": "You generate concise book categories using web-like topical reasoning. Output JSON only.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        content = response.choices[0].message.content or "{}"
        parsed = json.loads(content)
        categories = parsed.get("categories", [])
        # Keep max categories and normalize shape
        normalized = []
        for cat in categories[:MAX_CATEGORIES]:
            normalized.append(
                {
                    "name": cat.get("name", "General"),
                    "reason": cat.get("reason", "")[:160],
                    "search_terms": cat.get("search_terms", [])[:3],
                    "confidence": float(cat.get("confidence", 0.5)),
                }
            )
        return normalized
    except Exception as exc:
        logger.error(f"OpenAI failed for {product.get('title')}: {exc}")
        return []


def save_categories(product_id: str, categories: List[Dict[str, Any]]) -> bool:
    mutation = """
    mutation productUpdate($input: ProductInput!) {
      productUpdate(input: $input) {
        userErrors { field message }
        product { id }
      }
    }
    """
    payload = {
        "query": mutation,
        "variables": {
            "input": {
                "id": product_id,
                "metafields": [
                    {
                        "namespace": "custom",
                        "key": "book_categories",
                        "type": "json",
                        "value": json.dumps(
                            {
                                "source": "openai",
                                "model": OPENAI_MODEL,
                                "categories": categories,
                            }
                        ),
                    }
                ],
            }
        },
    }

    resp = requests.post(
        GRAPHQL_URL,
        headers={
            "X-Shopify-Access-Token": ACCESS_TOKEN,
            "Content-Type": "application/json",
        },
        json=payload,
    )
    if resp.status_code != 200:
        logger.error(f"Metafield update failed ({resp.status_code}): {resp.text}")
        return False

    data = resp.json()
    if "errors" in data:
        logger.error(f"GraphQL errors: {data['errors']}")
        return False

    user_errors = (
        data.get("data", {})
        .get("productUpdate", {})
        .get("userErrors", [])
    )
    if user_errors:
        logger.error(f"User errors: {user_errors}")
        return False
    return True


def process_all() -> Dict[str, Any]:
    products = fetch_products()
    total = len(products)
    logger.info(f"Found {total} products")

    updated = []
    skipped = []
    errors = []

    for idx, product in enumerate(products, start=1):
        product_id = product.get("id")
        title = product.get("title", "Untitled")
        handle = product.get("handle", "")

        existing_value = product.get("metafield", {}).get("value") if product.get("metafield") else None
        if existing_value and not OVERWRITE_EXISTING:
            logger.info(f"[{idx}/{total}] Skipping {title} (already has categories)")
            skipped.append({"id": product_id, "title": title, "handle": handle})
            continue

        logger.info(f"[{idx}/{total}] Generating categories for {title}")
        categories = generate_categories(product)
        if not categories:
            errors.append({"id": product_id, "title": title, "reason": "OpenAI returned no categories"})
            continue

        if save_categories(product_id, categories):
            logger.info(f"✅ Saved categories for {title}")
            updated.append(
                {
                    "id": product_id,
                    "title": title,
                    "handle": handle,
                    "categories": categories,
                }
            )
        else:
            logger.error(f"❌ Failed to save categories for {title}")
            errors.append({"id": product_id, "title": title, "reason": "Save failed"})

        time.sleep(0.25)  # gentle rate limit buffer

    summary = {
        "message": "Book categories generation completed",
        "total_products": total,
        "updated": len(updated),
        "skipped": len(skipped),
        "errors": len(errors),
        "overwrite_existing": OVERWRITE_EXISTING,
    }

    result = {"success": True, "summary": summary, "data": {"updated": updated, "skipped": skipped, "errors": errors}}
    print("RESULT_JSON:", json.dumps(result))
    return result


def main():
    try:
        process_all()
    except Exception as exc:
        logger.exception(f"Fatal error: {exc}")
        fail = {"success": False, "error": str(exc)}
        print("RESULT_JSON:", json.dumps(fail))


if __name__ == "__main__":
    main()
