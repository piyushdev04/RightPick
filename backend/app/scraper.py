from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

import requests

BASE_URL = "https://hunnit.com"


COLLECTION_URLS = [
    "/collections/half-sleeve-tops",
    "/collections/tank-top",
    "/collections/sweatshirts",
    "/collections/leggings",
    "/collections/skorts-for-women-1",
    "/collections/shorts",
    "/collections/joggers",
    "/collections/flare-pants",
    "/collections/capris",
    "/collections/straight-pants",
    "/collections/co-ord-set",
    "/collections/sports-bra",
    "/collections/jackets-hoodies",
]


ACTIVITY_MAP: Dict[str, List[str]] = {
    "tennis-pickel-golf": ["tennis", "pickleball", "golf", "medium-intensity"],
    "running": ["running", "high-endurance"],
    "casual": ["casual", "all-day"],
    "yoga": ["yoga", "low-impact"],
    "travel": ["travel", "on-the-go"],
    "hyrox": ["hyrox", "high-performance"],
    "pilates": ["pilates", "core-focused"],
    "gym": ["gym", "high-intensity"],
}

# Heuristic mapping from collection/category handle to usage tags.
# This approximates "shop by activity" so retrieval and reasoning work better.
CATEGORY_ACTIVITY_HINTS: Dict[str, List[str]] = {
    "sweatshirts": ["casual", "all-day", "meeting-friendly"],
    "joggers": ["casual", "travel", "gym"],
    "leggings": ["gym", "running", "yoga"],
    "shorts": ["gym", "running", "casual"],
    "skorts-for-women-1": ["tennis", "pickleball", "golf"],
    "sports-bra": ["gym", "training"],
    "co-ord-set": ["gym", "casual", "all-day"],
    "jackets-hoodies": ["travel", "casual", "all-day"],
    "flare-pants": ["casual", "meeting-friendly"],
    "straight-pants": ["casual", "meeting-friendly"],
}


@dataclass
class ScrapedProduct:
    title: str
    slug: str
    product_url: str
    price: Optional[float]
    currency: Optional[str]
    description: Optional[str]
    features: Optional[str]
    image_url: Optional[str]
    category: Optional[str]
    subcategory: Optional[str]
    activities: List[str]


def _fetch_collection_json(handle: str) -> dict:
    """
    Use Shopify JSON endpoint instead of brittle HTML scraping.

    Example:
      https://hunnit.com/collections/{handle}/products.json?limit=250
    """
    url = f"{BASE_URL}/collections/{handle}/products.json"
    params = {"limit": 250}
    resp = requests.get(url, params=params, timeout=20)
    resp.raise_for_status()
    return resp.json()


def _parse_price(value) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _extract_activity_tags_from_title(title: str) -> List[str]:
    title_lower = title.lower()
    tags: List[str] = []
    for slug, acts in ACTIVITY_MAP.items():
        if any(key in title_lower for key in acts):
            tags.extend(acts)
    return sorted(set(tags))


def scrape_collection(collection_path: str) -> List[ScrapedProduct]:
    """
    Scrape a collection using the Shopify JSON products endpoint.
    This is more stable and returns all products in the collection (up to 250).
    """
    # collection_path like "/collections/leggings" → handle "leggings"
    handle = collection_path.rstrip("/").split("/")[-1]
    data = _fetch_collection_json(handle)

    shopify_products = data.get("products", []) or []
    products: List[ScrapedProduct] = []

    for p in shopify_products:
        slug = p.get("handle") or ""
        if not slug:
            continue
        title = p.get("title") or slug.replace("-", " ").title()
        product_url = f"{BASE_URL}/products/{slug}"

        body_html = p.get("body_html") or ""
        # Treat full body_html as description; features could be extended later if needed
        description = body_html.strip() or None
        features = None

        variants = p.get("variants") or []
        price = _parse_price(variants[0].get("price") if variants else None)

        images = p.get("images") or []
        image_url = images[0].get("src") if images else None

        category = handle
        subcategory = p.get("product_type") or None

        tags_raw = p.get("tags") or ""
        if isinstance(tags_raw, str):
            tag_list = [t.strip() for t in tags_raw.split(",") if t.strip()]
        else:
            tag_list = [str(t).strip() for t in tags_raw if str(t).strip()]

        activities_from_title = _extract_activity_tags_from_title(title)
        activities_from_tags = _extract_activity_tags_from_title(" ".join(tag_list))
        base_activities = activities_from_title + activities_from_tags

        # Add heuristic category-based activity hints
        extra_from_category = CATEGORY_ACTIVITY_HINTS.get(category or "", [])
        activities = sorted(set(base_activities + extra_from_category))

        products.append(
            ScrapedProduct(
                title=title,
                slug=slug,
                product_url=product_url,
                price=price,
                currency="INR",
                description=description,
                features=features,
                image_url=image_url,
                category=category,
                subcategory=subcategory,
                activities=activities,
            )
        )

    return products


def scrape_all_collections() -> List[ScrapedProduct]:
    all_products: Dict[str, ScrapedProduct] = {}
    for path in COLLECTION_URLS:
        for p in scrape_collection(path):
            # use slug as dedup key
            all_products[p.slug] = p
    return list(all_products.values())


