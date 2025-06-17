# Mini RAG API

## Overview

Mini RAG API is a FastAPI application for advanced product search and recommendation. It combines semantic and hybrid search, LLM-powered query expansion, slot extraction, and reranking. The app integrates Qdrant, OpenAI, and other ML/NLP tools to provide relevant, context-aware product recommendations.

## Project Directory Structure

```
mini_rag/
├── app/
│   ├── api/
│   │   └── routes/
│   │       └── search.py         # API endpoints for product search
│   ├── core/
│   │   ├── config.py             # App configuration and environment variables
│   │   ├── models.py             # Pydantic models and enums
│   │   ├── prompts.py            # LLM prompt templates
│   │   └── utils.py              # Utility functions (e.g., type conversion)
│   ├── services/
│   │   └── search_service.py     # Core search, rerank, and LLM orchestration logic
│   └── main.py                   # FastAPI app entry point
├── README.md                     # Project documentation
├── requirements.txt              # Python dependencies
└── .env                          # Environment variables (not committed)
```

- **app/api/routes/**: FastAPI route definitions.
- **app/core/**: Configuration, data models, prompt templates, and utilities.
- **app/services/**: Business logic for search, reranking, and LLM integration.
- **app/main.py**: FastAPI application setup and middleware.
- **requirements.txt**: Python dependencies.
- **.env**: Environment variables for configuration.

## Features

- Multiple search pipelines: `SEMANTIC`, `FUSION_RRF`, `BM25_TO_SEMANTIC`, `SEMANTIC_TO_BM25`
- LLM-powered query expansion and slot extraction
- Cross-encoder reranking (optional)
- LLM-generated product recommendations
- Configurable models and endpoints via environment variables
- CORS enabled, `/health` endpoint, and performance logging

## API Endpoints

Base path: `/api/v1`

### `POST /api/v1/products/search`

- **Description:** Search for products and get LLM-powered recommendations.
- **Form Parameters:**
  - `query` (str, required): User's search query.
  - `limit` (int, default: 10)
  - `rerank_limit` (int, default: 10)
  - `pipeline` (str, default: "SEMANTIC")
  - `do_rerank` (bool, default: False)
- **Response:**
  ```json
  {
    "original_query": "string",
    "expanded_query": "string | null",
    "extracted_slots": { ... } | null,
    "status_message": "string",
    "recommended_products": {
      "response_type": "PRODUCT_LIST",
      "message_text": "string",
      "products": [
        {
          "product_id": "string",
          "name": "string",
          "product_url": "string",
          "thumbnail_url": "string",
          "description": "string"
        }
      ]
    } | null
  }
  ```

### `GET /api/v1/products/search`

- **Description:** Same as POST, but accepts query parameters.
- **Query Parameters:** Same as POST, defaults: `limit=30`, `pipeline="FUSION_RRF"`, `do_rerank=True`
- **Response:** Same as POST.

### `/health`

- **Description:** Health check endpoint.
- **Response:**
  ```json
  { "status": "ok" }
  ```

## Configuration

Set via environment variables or `.env` file:

- `QDRANT_URL`: Qdrant instance URL (default: `http://localhost:6333`)
- `COLLECTION_NAME`: Qdrant collection name
- `CROSS_ENCODER_MODEL`: Cross-encoder model (default: `svalabs/cross-electra-ms-marco-german-uncased`)
- `OPENAI_EMBEDDING_MODEL`: OpenAI embedding model (default: `text-embedding-3-large`)
- `LLM_MODEL`: OpenAI chat model (default: `gpt-4o-mini`)
- `OPENAI_API_KEY`: Your OpenAI API key

See `app/core/config.py` for all options.

## Running the Application

1. **Install dependencies:**  
   ```bash
   pip install -r requirements.txt
   ```
2. **Set environment variables:**  
   Create a `.env` file with your configuration.
3. **Run the app:**  
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
   ```

## Notes

- Uses FastAPI, Qdrant, OpenAI, Sentence Transformers, FastEmbed, and more.
- Logs to both console and `mini_RAG.log`.