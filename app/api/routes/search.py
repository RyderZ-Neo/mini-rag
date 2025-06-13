from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import JSONResponse

from app.core.models import SearchRequest, SearchResponse, OpenAIResponse
from app.services.search_service import process_search_query
from app.core.utils import convert_numpy_types

router = APIRouter()


@router.post("/search")  # Removed response_model constraint
async def search(search_request: SearchRequest):
    """
    Execute a search query and return OpenAI chat completion response
    
    - **query**: Text search query
    - **limit**: Maximum number of search results (default: 30)
    - **rerank_limit**: Maximum number of results to rerank (default: 10)
    - **pipeline**: Search pipeline to use (default: FUSION_RRF)
    """
    try:
        # Assuming process_search_query returns the OpenAI response
        openai_response = await process_search_query(
            query=search_request.query,
            limit=search_request.limit,
            rerank_limit=search_request.rerank_limit,
            pipeline=search_request.pipeline
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


@router.get("/search")  # Removed response_model constraint
async def search_get(
    query: str,
    limit: int = 30,
    rerank_limit: int = 10,
    pipeline: str = "FUSION_RRF"
):
    """
    Execute a search query with GET method and return OpenAI chat completion response
    
    - **query**: Text search query
    - **limit**: Maximum number of search results (default: 30)
    - **rerank_limit**: Maximum number of results to rerank (default: 10)
    - **pipeline**: Search pipeline to use (default: FUSION_RRF)
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
        pipeline=pipeline_enum
    )
    
    try:
        # Assuming process_search_query returns the OpenAI response
        openai_response = await process_search_query(
            query=request.query,
            limit=request.limit,
            rerank_limit=request.rerank_limit,
            pipeline=request.pipeline
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