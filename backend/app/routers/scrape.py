from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Product
from ..schemas import Product as ProductSchema
from ..scraper import ScrapedProduct, scrape_all_collections
from ..vectorstore import upsert_products


router = APIRouter(prefix="/scrape", tags=["scrape"])


@router.post("/run", response_model=List[ProductSchema])
def run_scraper(db: Session = Depends(get_db)):
    """
    Scrape all configured Hunnit collections and upsert into the DB.

    If a product with the same slug already exists, its fields (including
    activities) are updated so improvements to the scraper propagate.
    """
    scraped: List[ScrapedProduct] = scrape_all_collections()

    existing_by_slug = {
        p.slug: p for p in db.scalars(select(Product))  # type: ignore[arg-type]
    }

    upserted: List[Product] = []

    for sp in scraped:
        activities_str = ",".join(sp.activities)

        product = existing_by_slug.get(sp.slug)
        if product:
            # Update existing
            product.title = sp.title
            product.product_url = sp.product_url
            product.price = sp.price
            product.currency = sp.currency
            product.description = sp.description
            product.features = sp.features
            product.image_url = sp.image_url
            product.category = sp.category
            product.subcategory = sp.subcategory
            product.activities = activities_str
        else:
            # Insert new
            product = Product(
                title=sp.title,
                slug=sp.slug,
                product_url=sp.product_url,
                price=sp.price,
                currency=sp.currency,
                description=sp.description,
                features=sp.features,
                image_url=sp.image_url,
                category=sp.category,
                subcategory=sp.subcategory,
                activities=activities_str,
            )
            db.add(product)

        upserted.append(product)

    db.commit()
    for p in upserted:
        db.refresh(p)

    return upserted


@router.post("/index")
def index_products(db: Session = Depends(get_db)):
    products: List[Product] = list(db.scalars(select(Product)))
    if not products:
        return {"indexed": 0}

    upsert_products(
        product_ids=[p.id for p in products],
        titles=[p.title for p in products],
        descriptions=[p.description or "" for p in products],
        features_list=[p.features or "" for p in products],
        categories=[p.category or "" for p in products],
        activities_list=[
            [a.strip() for a in (p.activities or "").split(",") if a.strip()]
            for p in products
        ],
    )
    return {"indexed": len(products)}


