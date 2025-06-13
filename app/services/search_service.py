import os
import time
import logging
import datetime
import traceback
import json
from typing import Dict, List, Tuple, Any, Optional

import torch
import openai
from qdrant_client import QdrantClient, models
from fastembed import SparseTextEmbedding
from langchain_openai import OpenAIEmbeddings
from sentence_transformers import CrossEncoder

from app.core.config import settings
from app.core.models import SearchPipeline

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("mini_RAG.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("mini_RAG")

# Initialize OpenAI client
client = openai.OpenAI()

# Initialize BM25 embedding model
bm25_embedding_model = SparseTextEmbedding("Qdrant/bm25", language="german")

# Global variables for clients and models
qdrant_client = None
openai_embeddings = None
cross_encoder = None


def log_performance(operation, query, elapsed_time_ms, details=None):
    """Log performance metrics with timestamp"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    details_str = f", details: {details}" if details else ""
    logger.info(f"PERFORMANCE: {operation} for '{query}' took {elapsed_time_ms:.2f}ms{details_str}")


def get_openai_completion(prompt: str, operation_name: str, model: str = settings.LLM_MODEL) -> Optional[str]:
    """Get completion from OpenAI API and log its performance."""
    start_time = time.time()
    prompt_snippet = (prompt[:70] + '...') if len(prompt) > 70 else prompt # For concise logging
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            # store=True, # This parameter is not standard for openai.ChatCompletion.create
        )
        content = response.choices[0].message.content
        elapsed_ms = (time.time() - start_time) * 1000
        log_performance(operation_name, prompt_snippet, elapsed_ms, details=f"Model: {model}")
        return content
    except Exception as e:
        elapsed_ms = (time.time() - start_time) * 1000
        logger.error(f"OpenAI API Error during {operation_name} with model {model}: {e}")
        log_performance(operation_name, prompt_snippet, elapsed_ms, details=f"Model: {model}, Error: {str(e)}")
        return None


def initialize_models():
    """Initialize Qdrant client and embedding models"""
    global qdrant_client, openai_embeddings, cross_encoder
    if qdrant_client is None or openai_embeddings is None or cross_encoder is None:
        try:
            start_time = time.time()
            logger.info(f"Connecting to Qdrant at {settings.QDRANT_URL}...")
            qdrant_client = QdrantClient(url=settings.QDRANT_URL)
            
            logger.info(f"Initializing OpenAI embeddings ({settings.OPENAI_EMBEDDING_MODEL})...")
            openai_embeddings = OpenAIEmbeddings(model=settings.OPENAI_EMBEDDING_MODEL)
            
            logger.info(f"Loading cross-encoder model {settings.CROSS_ENCODER_MODEL}...")
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
            cross_encoder = CrossEncoder(
                settings.CROSS_ENCODER_MODEL, 
                device=device, 
                trust_remote_code=True, 
                activation_fn=torch.nn.Sigmoid()
            )
            
            elapsed_ms = (time.time() - start_time) * 1000
            log_performance("Initialization", "models_and_client", elapsed_ms)
            logger.info(f"Successfully initialized Qdrant client and models.")
        except Exception as e:
            logger.error(f"ERROR: Failed to initialize: {e}")
            qdrant_client = None
            openai_embeddings = None
            cross_encoder = None
            raise ConnectionError(f"Failed to initialize: {e}")
    # Add None as the fourth return value to match expected unpacking
    return qdrant_client, openai_embeddings, cross_encoder, None


def search_and_rerank(query, limit=30, rerank_limit=10, pipeline=SearchPipeline.FUSION_RRF):
    """Search Qdrant and rerank results using cross-encoder with selectable pipeline"""
    if not query:
        return [], [], "Error: Query is required."
    
    start_time = time.time()
    status_message = f"Searching for: {query}..."
    logger.info(f"Using search pipeline: {pipeline}")
    
    try:
        # Initialize clients and models
        client, embeddings_model, cross_encoder_model, _ = initialize_models()
        if client is None or embeddings_model is None or cross_encoder_model is None:
            return [], [], "Error: Failed to initialize models or client."
        
        # Encode query using OpenAI embeddings
        encode_start = time.time()
        query_vector = embeddings_model.embed_query(query)
        
        # Get BM25 vector if needed
        bm25_query = None
        if pipeline != SearchPipeline.SEMANTIC:
            bm25_query = next(bm25_embedding_model.query_embed(query))
            
        encode_elapsed = (time.time() - encode_start) * 1000
        log_performance("Query encoding", query, encode_elapsed)
        
        # Search in Qdrant
        search_start = time.time()
        
        # Select search parameters based on selected pipeline
        if pipeline == SearchPipeline.SEMANTIC:
            # Vanilla Semantic Search
            search_params = {
                "collection_name": settings.COLLECTION_NAME,
                "query": query_vector,
                "limit": limit,
                "with_payload": True,
                "using": "openai_text_embedding_large_v3",
            }
            
        elif pipeline == SearchPipeline.FUSION_RRF:
            # RRF Fusion Search
            prefetch = [
                models.Prefetch(
                    query=query_vector,
                    using="openai_text_embedding_large_v3",
                    limit=40,
                ),
                models.Prefetch(
                    query=models.SparseVector(**bm25_query.as_object()),
                    using="bm25",
                    limit=40,
                ),
            ]
            search_params = {    
                "collection_name": settings.COLLECTION_NAME,
                "query": models.FusionQuery(
                    fusion=models.Fusion.RRF
                ),
                "limit": limit,
                "with_payload": True,
                "prefetch": prefetch,
            }
            
        elif pipeline == SearchPipeline.BM25_TO_SEMANTIC:
            # 2-step: BM25 > Semantic Search
            prefetch = [
                models.Prefetch(
                    query=models.SparseVector(**bm25_query.as_object()),
                    using="bm25",
                    limit=50,
                ),
            ]
            search_params = {
                "prefetch": prefetch,
                "collection_name": settings.COLLECTION_NAME,
                "query": query_vector,
                "limit": limit,
                "with_payload": True,
                "using": "openai_text_embedding_large_v3",
            }
            
        elif pipeline == SearchPipeline.SEMANTIC_TO_BM25:
            # 2-step: Semantic Search > BM25
            prefetch = [
                models.Prefetch(
                    query=query_vector,
                    using="openai_text_embedding_large_v3",
                    limit=40,
                ),
            ]
            search_params = {
                "prefetch": prefetch,
                "collection_name": settings.COLLECTION_NAME,
                "query": models.SparseVector(**bm25_query.as_object()),
                "limit": limit,
                "with_payload": True,
                "using": "bm25",
            }
            
        # Get response from Qdrant
        response = client.query_points(**search_params)
        
        # Extract points from the response based on the schema
        if hasattr(response, 'result') and hasattr(response.result, 'points'):
            # If it's a structured response object
            hits = response.result.points
        elif hasattr(response, 'points'):
            # If it's the QueryResponse with points attribute
            hits = response.points
        else:
            # Try treating it as a dictionary (raw JSON response)
            try:
                hits = response.get('result', {}).get('points', [])
            except:
                logger.error("Couldn't extract points from response")
                hits = []
        
        search_elapsed = (time.time() - search_start) * 1000

        if not hits:
            elapsed_ms = (time.time() - start_time) * 1000
            status_message = f"No results found for '{query}'. ⏱️ [Search: {search_elapsed:.1f}ms]"
            log_performance("Search", query, elapsed_ms, "No results")
            return [], [], status_message

        # Process retrieved documents
        retrieved_docs = []
        for hit in hits:
            try:
                # Handle both object-style hits and dictionary-style hits
                if hasattr(hit, 'payload'):
                    # It's a structured Point object
                    point_id = hit.id
                    score = hit.score
                    payload = hit.payload
                elif isinstance(hit, dict):
                    # It's a dictionary
                    point_id = hit.get('id', 'unknown')
                    score = hit.get('score', 0)
                    payload = hit.get('payload', {})
                else:
                    logger.warning(f"Unknown hit type: {type(hit)}")
                    continue
                
                retrieved_docs.append({
                    'point_id': point_id,
                    'product_id': payload.get('product_id'),
                    'score': score,
                    'title': payload.get('title', 'No Title'),
                    'url': payload.get('url', 'No URL'),
                    'page_content': payload.get('page_content', ''),
                    'thumbnail': payload.get('thumbnail', payload.get('image', 'https://placeholder.com/150')),
                })
            except Exception as e:
                logger.error(f"Error processing hit: {e}")
                continue
                
        original_results = retrieved_docs.copy()
        
        # Rerank top results
        rerank_start = time.time()
        top_items_for_reranking = retrieved_docs[:rerank_limit]
        
        if top_items_for_reranking:
            sentence_pairs = [[query, item['page_content']] for item in top_items_for_reranking]
            rerank_scores = cross_encoder_model.predict(sentence_pairs)
            
            # Sort by new scores
            reranked_items = sorted(zip(rerank_scores, top_items_for_reranking), 
                                  key=lambda x: x[0], reverse=True)
            
            # Update retrieved docs with reranked ones
            final_results = []
            for score, item in reranked_items:
                item['rerank_score'] = score
                final_results.append(item)
            
            rerank_elapsed = (time.time() - rerank_start) * 1000
        else:
            final_results = retrieved_docs
            rerank_elapsed = 0
        
        elapsed_ms = (time.time() - start_time) * 1000
        status_message = (f"Found {len(hits)} results and reranked top {rerank_limit}. "
                         f"⏱️ [Search: {search_elapsed:.1f}ms, Rerank: {rerank_elapsed:.1f}ms, "
                         f"Total: {elapsed_ms:.1f}ms]")
        
        log_performance("Search and rerank", query, elapsed_ms, 
                      f"search: {search_elapsed:.1f}ms, rerank: {rerank_elapsed:.1f}ms, "
                      f"hits: {len(hits)}, reranked: {min(len(hits), rerank_limit)}")

        return original_results, final_results, status_message

    except Exception as e:
        elapsed_ms = (time.time() - start_time) * 1000
        error_msg = str(e)
        logger.error(f"Search error: {error_msg}")
        logger.error(traceback.format_exc())
        status_message = f"Error searching for '{query}': {error_msg}"
        log_performance("Search error", query, elapsed_ms, error_msg)
        return [], [], status_message


# Prompt templates
REWRITE_PROMPT = """
You are an expert at query understanding and expansion for e-commerce product search.

First, analyze the user's query: "{question}"

1. IDENTIFY INTENT: What is the user trying to accomplish? Are they looking for a specific product, comparing options, or seeking information?

2. EXTRACT SLOTS: Identify key entities in the query:
- Product type/category
- Specifications (memory, size, processor, etc.)
- Brand preferences
- Price indicators
- Usage requirements
- Any other constraints

3. GENERATE IMPROVED QUERIES: Create 5 variations of the original query that:
- Preserve the core intent
- Include all identified slots/entities
- Use relevant domain-specific terminology
- Add helpful context that might improve retrieval
- Expand abbreviations and use alternative terms

Return your analysis and queries in this format:

INTENT: [Core user intent]
SLOTS: [Key entity 1], [Key entity 2], [etc.]

QUERIES:
1. [First improved query]
2. [Second improved query]
3. [Third improved query]
4. [Fourth improved query]
5. [Fifth improved query with translation elements]
"""

PRODUCT_PROMPT = """### INSTRUCTION ###
You are a JSON generation bot. Your task is to populate the JSON object below using the provided context of several products.
- `response_type` must be "PRODUCT_LIST".
- `message_text` present the recommended options based on the query nicely and ask the user to choose from the options.
- The `products` array must contain an object for each and every product in the context.
- For each product, the `description` should be a compelling, benefit-focused sentence that highlights its standout feature in marketing language - focus on what makes this product special and why a customer would want it.
- Fill all fields from the context. Do not output anything other than the single JSON object.

### JSON SCHEMA ###
{{
"response_type": "PRODUCT_LIST",
"message_text": "string",
"products": [
    {{
    "id": "string",  
    "product_id": "string",
    "name": "string",
    "product_url": "string",
    "thumbnail_url": "string",
    "description": "string"
    }}
]
}}

### USER QUERY ###
{question}

### CONTEXT: PRODUCT DATA ###
{context}
"""

async def process_search_query(query: str, limit: int = 30, rerank_limit: int = 10, 
                        pipeline: SearchPipeline = SearchPipeline.FUSION_RRF) -> Dict[str, Any]:
    """Process a search query and return results with product recommendations"""
    overall_process_start_time = time.time()
    logger.info(f"Original User Query: {query}")
    
    # --- 1. Expand the query using LLM ---
    expansion_start_time = time.time()
    formatted_rewrite_prompt = REWRITE_PROMPT.format(question=query)
    expanded_query_response = get_openai_completion(
        prompt=formatted_rewrite_prompt,
        operation_name="OpenAI Query Expansion"
    )
    expansion_duration_ms = (time.time() - expansion_start_time) * 1000
    logger.info(f"Expanded Query Analysis: {expanded_query_response}")

    # Extract the actual queries from the structured response
    expanded_queries = []
    if expanded_query_response: # Check if the response is not None
        for line in expanded_query_response.split('\n'):
            if line.strip().startswith(('1.', '2.', '3.', '4.', '5.')):
                expanded_queries.append(line.strip()[3:].strip())  # Remove the number and whitespace
    else:
        logger.warning("OpenAI Query Expansion did not return a response.")

    # Use the first expanded query or fall back to the original
    query_to_use = expanded_queries[0] if expanded_queries else query
    logger.info(f"Using expanded query: {query_to_use}")
    
    # --- 2. Search and rerank ---
    search_rerank_start_time = time.time()
    original_results, final_results, status_message = search_and_rerank(
        query_to_use, limit, rerank_limit, pipeline
    )
    search_rerank_duration_ms = (time.time() - search_rerank_start_time) * 1000
    
    # Use the returned reranked results instead of original ones for better context
    retrieved_docs = final_results[:3] if final_results else []
    logging.info(f"Retrieved {retrieved_docs[0]}  for context.")
    products_json = None
    json_gen_duration_ms = 0  # Initialize in case this step is skipped
    if retrieved_docs:
        # Create a structured format for the LLM to parse into JSON
        structured_docs = []
        for i, doc in enumerate(retrieved_docs):
            doc_id = doc.get('point_id', f'product_{i+1}')
            product_id = doc.get('product_id')
            title = doc.get('title', 'No Title')
            url = doc.get('url', 'No URL')
            thumbnail = doc.get('thumbnail', doc.get('image', 'https://placeholder.com/150'))
            
            structured_entry = f"PRODUCT {i+1}:\n" \
                              f"ID: {doc_id}\n" \
                              f"PRODUCT_ID: {product_id}\n" \
                              f"NAME: {title}\n" \
                              f"URL: {url}\n" \
                              f"THUMBNAIL: {thumbnail}\n" \
                              f"CONTENT: {doc.get('page_content', '')}...\n"
            structured_docs.append(structured_entry)
        logging.info(f"Structured Documents for LLM: {structured_docs[0]}")
        # Join the structured documents
        docs_content = "\n\n" + "\n\n".join(structured_docs)
        
        # Format the prompt with the query and context
        formatted_prompt = PRODUCT_PROMPT.format(
            question=query_to_use, context=docs_content
        )
        
        # --- 3. Get the structured response using get_openai_completion ---
        json_gen_start_time = time.time()
        answer_content = get_openai_completion(
            prompt=formatted_prompt,
            operation_name="OpenAI Product JSON Generation"
        )
        json_gen_duration_ms = (time.time() - json_gen_start_time) * 1000
        
        logger.info(f"Final Query Used: {query_to_use}")
        logger.info(f"Answer: {answer_content}")

        try:
            if answer_content: # Check if answer_content is not None
                products_json = json.loads(answer_content)
            else:
                logger.error("OpenAI Product JSON Generation did not return content.")
                products_json = None # Ensure products_json is None if no content
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON response: {e}")
            logger.error(f"Raw response: {answer_content}")
    
    # Construct the API response
    response = {
        "original_query": query,
        "expanded_query": query_to_use if query_to_use != query else None,
        "status_message": status_message,
        "recommended_products": products_json
    }

    total_process_duration_ms = (time.time() - overall_process_start_time) * 1000
    logger.info(
        f"PERFORMANCE SUMMARY for '{query}': \n"
        f"  Total process time: {total_process_duration_ms:.2f}ms\n"
        f"  Query Expansion: {expansion_duration_ms:.2f}ms\n"
        f"  Search & Rerank: {search_rerank_duration_ms:.2f}ms\n"
        f"  Product JSON Generation: {json_gen_duration_ms:.2f}ms"
    )
    
    return response