from dataclasses import dataclass

from langchain_core.documents import Document
from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer

from app.config import settings


@dataclass(frozen=True)
class RetrievalResult:
    document: Document
    score: float


class DocumentRetriever:
    def __init__(self) -> None:
        self.encoder = SentenceTransformer(
            settings.embedding_model,
            device="cpu",
        )

        self.client = QdrantClient(
            url=settings.qdrant_url,
            timeout=30,
        )

    def retrieve(
        self,
        query: str,
        top_k: int = 3,
    ) -> list[RetrievalResult]:
        query = query.strip()

        if not query:
            raise ValueError("Query must not be empty")

        if top_k <= 0:
            raise ValueError("top_k must be greater than zero")

        token_ids = self.encoder.tokenizer(
            query,
            truncation=False,
        )["input_ids"]

        if len(token_ids) > self.encoder.max_seq_length:
            raise ValueError("Query exceeds the embedding input limit")

        query_vector = self.encoder.encode(
            query,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )

        response = self.client.query_points(
            collection_name=settings.collection_name,
            query=query_vector.tolist(),
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="metadata.status",
                        match=models.MatchValue(value="active"),
                    ),
                    models.FieldCondition(
                        key="metadata.embedding_model",
                        match=models.MatchValue(
                            value=settings.embedding_model
                        ),
                    ),
                ]
            ),
            limit=top_k,
            with_payload=True,
            with_vectors=False,
        )

        results = []

        for point in response.points:
            payload = point.payload

            if (
                not payload
                or "page_content" not in payload
                or "metadata" not in payload
            ):
                raise ValueError(
                    f"Point {point.id} is missing document payload"
                )

            results.append(
                RetrievalResult(
                    document=Document(
                        page_content=payload["page_content"],
                        metadata=payload["metadata"],
                    ),
                    score=point.score,
                )
            )

        return results

    def close(self) -> None:
        self.client.close()