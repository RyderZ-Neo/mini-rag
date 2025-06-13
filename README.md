# Mini RAG API

## Description

**Mini RAG API** is a FastAPI-based application designed for searching and retrieving personalized product recommendations. It leverages various search pipelines, including semantic search with OpenAI embeddings, BM25, and fusion search techniques, to provide relevant results. The API also incorporates query expansion using large language models (LLMs) and reranking of search results to enhance precision.

## Features

*   **Advanced Search Capabilities**:
    *   Semantic search using OpenAI embeddings.
    *   BM25 sparse vector search.
    *   Hybrid search using Reciprocal Rank Fusion (RRF).
    *   2-Step pipelines (e.g., BM25 then Semantic, Semantic then BM25).
*   **Query Expansion**: Utilizes an LLM (e.g., GPT-4o-mini) to understand user intent, extract key entities, and generate improved search queries.
*   **Reranking**: Employs a cross-encoder model to rerank the top search results for improved relevance.
*   **Product Recommendations**: Generates structured JSON output for product recommendations based on search results.
*   **Configurable Pipelines**: Allows selection of different search pipelines via API requests.
*   **FastAPI Framework**: Built with FastAPI for high performance and automatic interactive API documentation (Swagger UI and ReDoc).
*   **Pydantic Models**: Ensures robust data validation for requests and responses.
*   **Asynchronous Operations**: Leverages FastAPI's async capabilities for non-blocking I/O.

## Technologies Used

*   **Backend**: Python, FastAPI
*   **Data Validation**: Pydantic
*   **Vector Database**: Qdrant
*   **Embeddings**:
    *   OpenAI Embeddings (e.g., `text-embedding-3-large`)
    *   FastEmbed (for BM25: `Qdrant/bm25`)
*   **Reranking**: Sentence Transformers (Cross-Encoder, e.g., `svalabs/cross-electra-ms-marco-german-uncased`)
*   **LLM for Query Expansion & JSON Generation**: OpenAI (e.g., `gpt-4o-mini`)
*   **ASGI Server**: Uvicorn

## Project Structure

```
mini_rag/
├── app/
│   ├── api/
│   │   └── routes/
│   │       └── search.py       # Search API endpoints
│   ├── core/
│   │   ├── config.py         # Application configuration settings
│   │   ├── models.py         # Pydantic models for requests and responses
│   │   └── utils.py          # Utility functions
│   ├── services/
│   │   └── search_service.py # Core search logic, model initialization, LLM interaction
│   └── main.py               # FastAPI application entry point
├── .env                      # Environment variables (API keys, Qdrant URL, etc.) - NOT versioned
├── .gitignore                # Specifies intentionally untracked files
└── README.md                 # This file
```

## Setup and Installation

1.  **Clone the repository (if applicable):**
    ```bash
    git clone <your-repository-url>
    cd mini_rag
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies:**
    Create a `requirements.txt` file with all necessary packages (e.g., `fastapi`, `uvicorn`, `pydantic`, `pydantic-settings`, `qdrant-client`, `openai`, `fastembed`, `sentence-transformers`, `torch`, `numpy`, `python-dotenv`).
    Then run:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up Environment Variables:**
    Create a `.env` file in the root directory (`/home/damon/mini_rag/.env`) and add your configuration. Refer to `app/core/config.py` for required variables.
    Example `.env` content:
    ```env
    QDRANT_URL="http://localhost:6333"
    COLLECTION_NAME="your_qdrant_collection_name"
    OPENAI_API_KEY="your_openai_api_key"
    # Optional: Override default models
    # CROSS_ENCODER_MODEL="svalabs/cross-electra-ms-marco-german-uncased"
    # OPENAI_EMBEDDING_MODEL="text-embedding-3-large"
    # LLM_MODEL="gpt-4o-mini"
    ```
    *Ensure your Qdrant instance is running and accessible at the specified `QDRANT_URL`.*

## Running the Application

To run the FastAPI application locally, use Uvicorn:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

*   `app.main:app`: Points to the FastAPI `app` instance in the `app/main.py` file.
*   `--host 0.0.0.0`: Makes the server accessible on your network.
*   `--port 8000`: Specifies the port to run on.
*   `--reload`: Enables auto-reloading when code changes (useful for development).

Once running, you can access the API:

*   **API Documentation (Swagger UI)**: `http://localhost:8000/docs`
*   **Alternative API Documentation (ReDoc)**: `http://localhost:8000/redoc`
*   **Health Check**: `http://localhost:8000/health`

## API Endpoints

All product-related search endpoints are prefixed with `/api/v1/products`.

### Health Check

*   **GET `/health`**
    *   Description: Checks the health status of the API.
    *   Response: `{"status": "ok"}`

### Search

*   **POST `/api/v1/products/search`**
    *   Description: Executes a search query using the specified pipeline and returns an OpenAI chat completion style response which includes product recommendations.
    *   Request Body: `SearchRequest` model ([app/core/models.py](app/core/models.py))
        ```json
        {
            "query": "your search query",
            "limit": 30,
            "rerank_limit": 10,
            "pipeline": "FUSION_RRF" // Or SEMANTIC, BM25_TO_SEMANTIC, SEMANTIC_TO_BM25
        }
        ```
    *   Response: A JSON object containing the original query, expanded query (if any), status message, and recommended products. (See `process_search_query` in [app/services/search_service.py](app/services/search_service.py) for response structure).

*   **GET `/api/v1/products/search`**
    *   Description: Executes a search query via GET request parameters.
    *   Query Parameters:
        *   `query` (str, required): The search query.
        *   `limit` (int, optional, default: 30): Maximum number of search results.
        *   `rerank_limit` (int, optional, default: 10): Maximum number of results to rerank.
        *   `pipeline` (str, optional, default: "FUSION_RRF"): The search pipeline to use (e.g., "SEMANTIC", "FUSION_RRF").
    *   Response: Same structure as the POST endpoint.

## Configuration

Application configuration is managed via environment variables and Pydantic settings in `app/core/config.py`. Key configurations include:

*   `API_V1_STR`: API version string.
*   `PROJECT_NAME`: Name of the project.
*   `QDRANT_URL`: URL of the Qdrant instance.
*   `COLLECTION_NAME`: Name of the Qdrant collection.
*   `CROSS_ENCODER_MODEL`: Model name for the cross-encoder.
*   `OPENAI_EMBEDDING_MODEL`: Model name for OpenAI embeddings.
*   `LLM_MODEL`: Model name for the LLM used in query expansion and JSON generation.
*   `OPENAI_API_KEY`: Your OpenAI API key (loaded from the environment).

Make sure to set these in your `.env` file.

## Logging

The application uses Python's built-in `logging` module.
*   Basic configuration is set in `app/main.py`.
*   The `search_service.py` configures a `FileHandler` to log to `mini_RAG.log` and a `StreamHandler` for console output. Performance metrics and errors are logged here.

---

This README provides a comprehensive overview of the Mini RAG API project. You can expand on sections like "Deployment" or "Detailed Pipeline Explanations" as the