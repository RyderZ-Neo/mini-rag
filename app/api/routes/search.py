from fastapi import APIRouter, HTTPException, status, Depends, Form
from fastapi.responses import JSONResponse
from typing import Optional

from app.core.models import SearchResponse, OpenAIResponse, SearchPipeline
from app.services.search_service import process_search_query
from app.core.utils import convert_numpy_types

router = APIRouter()

@router.post("/search")
async def search(
    query: str = Form(..., description="Search query text"),
    limit: Optional[int] = Form(10, description="Maximum number of results to return"),
    rerank_limit: Optional[int] = Form(10, description="Maximum number of results to rerank"),
    pipeline: Optional[str] = Form("SEMANTIC", description="Search pipeline to use"),
    do_rerank: Optional[bool] = Form(False, description="Whether to rerank the search results")
):
    """
    Execute a search query and return OpenAI chat completion response
    
    Form parameters:
    - **query**: Text search query
    - **limit**: Maximum number of search results (default: 30)
    - **rerank_limit**: Maximum number of results to rerank (default: 10)
    - **pipeline**: Search pipeline to use (default: FUSION_RRF)
    - **do_rerank**: Whether to rerank search results (default: True)
    """
    try:
        # Convert string pipeline parameter to enum
        try:
            pipeline_enum = getattr(SearchPipeline, pipeline)
        except (AttributeError, ValueError):
            pipeline_enum = SearchPipeline.FUSION_RRF
            
        # Process the search query
        openai_response = await process_search_query(
            query=query,
            limit=limit,
            rerank_limit=rerank_limit,
            pipeline=pipeline_enum,
            do_rerank=do_rerank
        )
        
        # Convert NumPy types to standard Python types for JSON serialization
        converted_response = convert_numpy_types(openai_response)
        
        # Return the processed response
        return converted_response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing search: {str(e)}"
        )

# Keep the GET endpoint the same
@router.get("/search")
async def search_get(
    query: str,
    limit: int = 30,
    rerank_limit: int = 10,
    pipeline: str = "FUSION_RRF",
    do_rerank: bool = True
):
    """
    Execute a search query with GET method and return OpenAI chat completion response
    
    - **query**: Text search query
    - **limit**: Maximum number of search results (default: 30)
    - **rerank_limit**: Maximum number of results to rerank (default: 10)
    - **pipeline**: Search pipeline to use (default: FUSION_RRF)
    - **do_rerank**: Whether to rerank search results (default: True)
    """
    # Convert string pipeline parameter to enum
    from app.core.models import SearchPipeline
    try:
        pipeline_enum = getattr(SearchPipeline, pipeline)
    except (AttributeError, ValueError):
        pipeline_enum = SearchPipeline.FUSION_RRF
        
    request = SearchRequest(
        query=query,
        limit=limit,
        rerank_limit=rerank_limit,
        pipeline=pipeline_enum,
        do_rerank=do_rerank
    )
    
    try:
        # Assuming process_search_query returns the OpenAI response
        openai_response = await process_search_query(
            query=request.query,
            limit=request.limit,
            rerank_limit=request.rerank_limit,
            pipeline=request.pipeline,
            do_rerank=request.do_rerank
        )
        
        # Convert NumPy types to standard Python types for JSON serialization
        converted_response = convert_numpy_types(openai_response)
        
        # Return the processed response
        return converted_response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing search: {str(e)}"
        )