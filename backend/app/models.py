from sqlalchemy import Column, Float, Integer, String, Text

from .database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    # Basic info
    title = Column(String(255), nullable=False, index=True)
    slug = Column(String(255), nullable=False, unique=True, index=True)
    product_url = Column(String(500), nullable=False)
    price = Column(Float, nullable=True)
    currency = Column(String(8), nullable=True, default="INR")

    # Content
    description = Column(Text, nullable=True)
    features = Column(Text, nullable=True)  # newline- or bullet-separated

    # Media
    image_url = Column(String(500), nullable=True)

    # Categories / tags
    category = Column(String(255), nullable=True)
    subcategory = Column(String(255), nullable=True)
    activities = Column(String(255), nullable=True)  # comma-separated activities


