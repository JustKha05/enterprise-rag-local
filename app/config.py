import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    qdrant_url: str = os.getenv(
        "QDRANT_URL", "http://localhost:6333"
    )
    ollama_url: str = os.getenv(
        "OLLAMA_URL", "http://localhost:11434"
    )
    generation_model: str = os.getenv(
        "GENERATION_MODEL", "phi4-mini:3.8b"
    )

    embedding_model: str = os.getenv(
        "EMBEDDING_MODEL",
        "sentence-transformers/all-MiniLM-L6-v2",
    )
    collection_name: str = os.getenv(
        "QDRANT_COLLECTION",
        "enterprise_docs_minilm_v1",
    )
    
settings = Settings()