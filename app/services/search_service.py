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
from app.core.prompts import REWRITE_PROMPT, PRODUCT_PROMPT # Import necessary prompts


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

def _extract_json_string_from_llm_output(llm_output: Optional[str]) -> Optional[str]:
    """
    Cleans the raw string output from an LLM, attempting to extract a valid JSON string.
    Removes common Markdown fences (e.g., ```json ... ```) and trims whitespace.
    """
    if not llm_output:
        return None
    
    cleaned_json = llm_output.strip()
    
    # Handle potential ```json prefix (and similar variations like ```)
    if cleaned_json.startswith("```json"):
        cleaned_json = cleaned_json[7:] # Length of "```json"
    elif cleaned_json.startswith("```"):
        cleaned_json = cleaned_json[3:] # Length of "```"
    
    # Strip again in case the prefix removal left whitespace or if there was no prefix
    cleaned_json = cleaned_json.strip()
    
    # Handle potential ``` suffix
    if cleaned_json.endswith("```"):
        cleaned_json = cleaned_json[:-3] # Length of "```"
        
    # Final strip to clean up any remaining whitespace
    cleaned_json = cleaned_json.strip()
    
    # Return the cleaned string; it might be empty if original was just fences/whitespace
    return cleaned_json if cleaned_json else None

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


def search_and_rerank(query, limit=50, rerank_limit=10, pipeline="SEMANTIC", do_rerank=True):
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
                    limit=30,
                ),
                models.Prefetch(
                    query=models.SparseVector(**bm25_query.as_object()),
                    using="bm25",
                    limit=30,
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
        
        # Rerank top results only if do_rerank is True
        rerank_elapsed = 0
        final_results = original_results # Default to original results if no reranking
        
        if do_rerank and rerank_limit > 0:
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
        
        elapsed_ms = (time.time() - start_time) * 1000
        
        # Update status message based on whether reranking was performed
        if do_rerank:
            status_message = (f"Found {len(hits)} results and reranked top {rerank_limit}. "
                             f"⏱️ [Search: {search_elapsed:.1f}ms, Rerank: {rerank_elapsed:.1f}ms, "
                             f"Total: {elapsed_ms:.1f}ms]")
        else:
            status_message = (f"Found {len(hits)} results (no reranking). "
                             f"⏱️ [Search: {search_elapsed:.1f}ms, Total: {elapsed_ms:.1f}ms]")
        
        # Log performance with appropriate message based on reranking status
        if do_rerank:
            log_performance("Search and rerank", query, elapsed_ms, 
                          f"search: {search_elapsed:.1f}ms, rerank: {rerank_elapsed:.1f}ms, "
                          f"hits: {len(hits)}, reranked: {min(len(hits), rerank_limit)}")
        else:
            log_performance("Search without rerank", query, elapsed_ms, 
                          f"search: {search_elapsed:.1f}ms, hits: {len(hits)}")

        return original_results, final_results, status_message

    except Exception as e:
        elapsed_ms = (time.time() - start_time) * 1000
        error_msg = str(e)
        logger.error(f"Search error: {error_msg}")
        logger.error(traceback.format_exc())
        status_message = f"Error searching for '{query}': {error_msg}"
        log_performance("Search error", query, elapsed_ms, error_msg)
        return [], [], status_message
    

async def process_search_query(query: str, limit: int = 30, rerank_limit: int = 10, 
                        pipeline: SearchPipeline = SearchPipeline.FUSION_RRF,
                        do_rerank: bool = True) -> Dict[str, Any]:
    """Process a search query and return results with product recommendations"""
    overall_process_start_time = time.time()
    logger.info(f"Original User Query: {query}")
    
    # --- 1. Expand the query using LLM ---
    expansion_start_time = time.time()
    formatted_rewrite_prompt = REWRITE_PROMPT.format(question=query)
    raw_expanded_query_response_str = get_openai_completion(
        prompt=formatted_rewrite_prompt,
        operation_name="OpenAI Query Expansion"
    )
    expansion_duration_ms = (time.time() - expansion_start_time) * 1000
    logger.info(f"Raw Expanded Query Response from LLM: {raw_expanded_query_response_str}")

    expanded_query_data = None
    slots = None
    query_to_use = query # Default to original query

    if raw_expanded_query_response_str:
        cleaned_json_for_expansion = _extract_json_string_from_llm_output(raw_expanded_query_response_str)
        if cleaned_json_for_expansion:
            try:
                expanded_query_data = json.loads(cleaned_json_for_expansion)
                
                improved_query_from_llm = expanded_query_data.get("improved_query")
                if improved_query_from_llm and isinstance(improved_query_from_llm, str) and improved_query_from_llm.strip():
                    query_to_use = improved_query_from_llm
                else:
                    logger.warning("No 'improved_query' in parsed LLM expansion or empty. Using original query.")

                extracted_slots = expanded_query_data.get("slots")
                if isinstance(extracted_slots, dict):
                    slots = extracted_slots
                else:
                    logger.warning(f"'slots' in LLM expansion is not a dict or missing. Using empty slots. Received: {extracted_slots}")
                
                logger.info(f"Successfully parsed expanded query. Using: '{query_to_use}'. Slots: {slots}")

            except json.JSONDecodeError as e:
                logger.error(f"Error parsing JSON from query expansion: {e}. Cleaned string: '{cleaned_json_for_expansion}'. Raw response: '{raw_expanded_query_response_str}'")
            except Exception as e: 
                logger.error(f"Unexpected error processing expanded query response: {e}. Cleaned string: '{cleaned_json_for_expansion}'. Raw response: '{raw_expanded_query_response_str}'")
        else:
            logger.warning("Query expansion response was empty after cleaning. Using original query.")
    else:
        logger.warning("OpenAI Query Expansion returned no response. Using original query.")
    
    logger.info(f"Using query for search: {query_to_use}")
    logger.info(f"Slots extracted: {slots if slots else 'None'}")
    # --- 2. Search and rerank ---
    search_rerank_start_time = time.time()
    original_results, final_results, status_message = search_and_rerank(
        query_to_use, limit, rerank_limit, pipeline, do_rerank
    )
    search_rerank_duration_ms = (time.time() - search_rerank_start_time) * 1000
    
    # # Use the returned reranked results instead of original ones for better context
    # retrieved_docs = final_results[:rerank_limit] if final_results else []
    # Use original search results for context
    retrieved_docs = original_results[:10] if original_results else [] # Testing with top 10 results with reranking for context
    # logging.info(f"Retrieved {retrieved_docs[0]} as first item out of {len(retrieved_docs)} for context.")
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
        # logging.info(f"Structured Documents for LLM: {structured_docs}")
        # Join the structured documents
        docs_content = "\n\n" + "\n\n".join(structured_docs)
        logging.info(f"First Structured document for context {docs_content}...")
        # need slots to be a JSON string for the prompt
        slots_json_str = json.dumps(slots if isinstance(slots, dict) else {})

        # Format the prompt with the query and context
        formatted_prompt = PRODUCT_PROMPT.format(
            question=query_to_use, context=docs_content, slots_json=slots_json_str, # Pass the JSON string of slots

        )
        
        # --- 3. Get the structured response using get_openai_completion ---
        json_gen_start_time = time.time()
        raw_product_json_response = get_openai_completion(
            prompt=formatted_prompt,
            operation_name="OpenAI Product JSON Generation"
        )
        json_gen_duration_ms = (time.time() - json_gen_start_time) * 1000
        
        logger.info(f"Final Query Used: {query_to_use}")
        logger.info(f"Answer: {raw_product_json_response}")

    if raw_product_json_response:
            cleaned_json_for_products = _extract_json_string_from_llm_output(raw_product_json_response)
            if cleaned_json_for_products:
                try:
                    products_json = json.loads(cleaned_json_for_products)
                except json.JSONDecodeError as e:
                    logger.error(f"Error parsing JSON response for products: {e}. Cleaned string: '{cleaned_json_for_products}'. Raw response: '{raw_product_json_response}'")
            else:
                logger.error("Product JSON response was empty after cleaning.")
    else:
            logger.error("OpenAI Product JSON Generation returned no response.")
            
    # Construct the API response
    response = {
        "original_query": query,
        "expanded_query": query_to_use if query_to_use != query else None,
        "extracted_slots": slots if slots else None,
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