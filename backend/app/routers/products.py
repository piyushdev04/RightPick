from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Product as ProductModel
from ..schemas import Product as ProductSchema
from ..schemas import ProductListResponse


router = APIRouter(prefix="/products", tags=["products"])


def _to_schema(model: ProductModel) -> ProductSchema:
  """Convert SQLAlchemy model → Pydantic schema with parsed activities list."""
  activities = [
      a.strip()
      for a in (model.activities or "").split(",")
      if a.strip()
  ]
  return ProductSchema(
      id=model.id,
      title=model.title,
      slug=model.slug,
      product_url=model.product_url,
      price=model.price,
      currency=model.currency,
      description=model.description,
      features=model.features,
      image_url=model.image_url,
      category=model.category,
      subcategory=model.subcategory,
      activities=activities,
  )


@router.get("", response_model=ProductListResponse)
def list_products(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    total = db.scalar(select(func.count()).select_from(ProductModel)) or 0
    stmt = select(ProductModel).offset(skip).limit(limit)
    models: List[ProductModel] = list(db.scalars(stmt))
    items = [_to_schema(m) for m in models]
    return ProductListResponse(total=total, items=items)


@router.get("/{product_id}", response_model=ProductSchema)
def get_product(product_id: int, db: Session = Depends(get_db)):
    model = db.get(ProductModel, product_id)
    if not model:
        raise HTTPException(status_code=404, detail="Product not found")
    return _to_schema(model)


