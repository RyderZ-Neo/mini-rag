from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, RootModel



class SearchPipeline(str, Enum):
    SEMANTIC = "SEMANTIC"
    FUSION_RRF = "FUSION_RRF"
    BM25_TO_SEMANTIC = "BM25_TO_SEMANTIC"
    SEMANTIC_TO_BM25 = "SEMANTIC_TO_BM25"

class SearchRequest(BaseModel):
    query: str = Field(..., description="Search query text")
    limit: int = Field(10, description="Maximum number of results to return")
    rerank_limit: int = Field(10, description="Maximum number of results to rerank")
    pipeline: SearchPipeline = Field(
        default=SearchPipeline.SEMANTIC, 
        description="Search pipeline to use"
    )
    do_rerank: bool = Field(
        default=False,
        description="Whether to rerank the search results"
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