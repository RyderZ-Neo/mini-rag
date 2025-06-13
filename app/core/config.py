import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Mini RAG API"
    
    # Model paths and configurations
    QDRANT_URL: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    COLLECTION_NAME: str = os.getenv("COLLECTION_NAME", "shop_api_openai_embeddings_collection")
    CROSS_ENCODER_MODEL: str = os.getenv("CROSS_ENCODER_MODEL", "svalabs/cross-electra-ms-marco-german-uncased")
    OPENAI_EMBEDDING_MODEL: str = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-large")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
    
    # OpenAI API key will be loaded from the environment
    # or from .env file with python-dotenv if installed

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()