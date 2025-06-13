from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, RootModel


class SearchPipeline(str, Enum):
    SEMANTIC = "Semantic Search (OpenAI Embeddings)"
    FUSION_RRF = "Fusion Search (RRF)"
    BM25_TO_SEMANTIC = "2-Step: BM25 → Semantic"
    SEMANTIC_TO_BM25 = "2-Step: Semantic → BM25"


class SearchRequest(BaseModel):
    query: str = Field(..., description="Search query text")
    limit: int = Field(30, description="Maximum number of results to return")
    rerank_limit: int = Field(10, description="Maximum number of results to rerank")
    pipeline: SearchPipeline = Field(
        default=SearchPipeline.FUSION_RRF, 
        description="Search pipeline to use"
    )


class Product(BaseModel):
    product_id: str
    name: str
    product_url: str
    thumbnail_url: str
    description: str


class ProductListResponse(BaseModel):
    response_type: str = "PRODUCT_LIST"
    message_text: str
    products: List[Product]


class SearchResult(BaseModel):
    id: str
    score: float
    title: str
    url: str
    page_content: str
    thumbnail: str
    rerank_score: Optional[float] = None


class SearchResponse(BaseModel):
    original_query: str
    expanded_query: Optional[str] = None
    results: List[SearchResult]
    status_message: str
    products: Optional[ProductListResponse] = None


class OpenAIResponse(RootModel):
    """Model to represent raw OpenAI API responses"""
    root: Dict[str, Any]
    
    class Config:
        arbitrary_types_allowed = True