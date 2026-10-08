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


settings = Settings()