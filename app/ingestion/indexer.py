from uuid import NAMESPACE_URL, uuid5

from langchain_core.documents import Document
from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer

from app.config import settings


def index_chunks(chunks: list[Document]) -> int:
    if not chunks:
        raise ValueError("No chunks to index")

    encoder = SentenceTransformer(
        settings.embedding_model,
        device="cpu",
    )

    texts = [chunk.page_content for chunk in chunks]

    # Avoid silently truncating chunks that exceed the model's limit.
    for chunk in chunks:
        token_ids = encoder.tokenizer(
            chunk.page_content,
            truncation=False,
        )["input_ids"]

        if len(token_ids) > encoder.max_seq_length:
            raise ValueError(
                f"{chunk.metadata['chunk_id']} exceeds the embedding "
                f"input limit. Reduce chunk_size and run again."
            )

    vectors = encoder.encode(
        texts,
        batch_size=16,
        normalize_embeddings=True,
        show_progress_bar=True,
        convert_to_numpy=True,
    )

    vector_size = vectors.shape[1]
    print(f"Embedding model: {settings.embedding_model}")
    print(f"Vector dimensions: {vector_size}")

    client = QdrantClient(
        url=settings.qdrant_url,
        timeout=30,
    )

    try:
        if not client.collection_exists(settings.collection_name):
            client.create_collection(
                collection_name=settings.collection_name,
                vectors_config=models.VectorParams(
                    size=vector_size,
                    distance=models.Distance.COSINE,
                ),
            )
        else:
            info = client.get_collection(settings.collection_name)
            vector_config = info.config.params.vectors

            if not isinstance(vector_config, models.VectorParams):
                raise ValueError("Expected a single unnamed vector")

            if (
                vector_config.size != vector_size
                or vector_config.distance != models.Distance.COSINE
            ):
                raise ValueError(
                    "Collection vector configuration does not match"
                )

        points = []

        for chunk, vector in zip(chunks, vectors, strict=True):
            point_id = str(
                uuid5(
                    NAMESPACE_URL,
                    f"{settings.collection_name}/{chunk.metadata['chunk_id']}",
                )
            )

            points.append(
                models.PointStruct(
                    id=point_id,
                    vector=vector.tolist(),
                    payload={
                        "page_content": chunk.page_content,
                        "metadata": {
                            **chunk.metadata,
                            "embedding_model": settings.embedding_model,
                        },
                    },
                )
            )

        client.upsert(
            collection_name=settings.collection_name,
            points=points,
            wait=True,
        )

        total = client.count(
            collection_name=settings.collection_name,
            exact=True,
        ).count

        print(f"Collection: {settings.collection_name}")
        print(f"Total stored points: {total}")

        return len(points)

    finally:
        client.close()