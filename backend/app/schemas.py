from typing import List, Optional

from pydantic import BaseModel, HttpUrl


class ProductBase(BaseModel):
    title: str
    slug: str
    product_url: HttpUrl
    price: Optional[float] = None
    currency: Optional[str] = "INR"
    description: Optional[str] = None
    features: Optional[str] = None
    image_url: Optional[HttpUrl] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    activities: List[str] = []


class ProductCreate(ProductBase):
    pass


class Product(ProductBase):
    id: int

    class Config:
        orm_mode = True


class ProductListResponse(BaseModel):
    total: int
    items: List[Product]


class ChatRequest(BaseModel):
    message: str
    top_k: int = 8


class ChatProductSnippet(BaseModel):
    id: int
    title: str
    price: Optional[float] = None
    image_url: Optional[HttpUrl] = None
    product_url: HttpUrl
    category: Optional[str] = None
    activities: List[str] = []
    relevance_score: float
    reason: Optional[str] = None


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatResponse(BaseModel):
    messages: List[ChatMessage]
    products: List[ChatProductSnippet]


