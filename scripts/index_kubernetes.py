from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer

from app.config import settings
from app.ingestion.indexer import index_chunks
from app.ingestion.technical_markdown_loader import (
    load_technical_markdown,
)


KUBERNETES_COLLECTION = "kubernetes_minilm_v1"


def main() -> None:
    if settings.collection_name != KUBERNETES_COLLECTION:
        raise SystemExit(
            f"ERROR: Set QDRANT_COLLECTION to {KUBERNETES_COLLECTION}"
        )

    project_root = Path(__file__).resolve().parents[1]
    source_dir = project_root / "data" / "raw" / "kubernetes"

    document = load_technical_markdown(
        markdown_path=source_dir / "deployment.md",
        metadata_path=source_dir / "deployment.metadata.json",
        project_root=project_root,
    )

    if document.metadata["unresolved_shortcodes"]:
        raise ValueError("Resolve all Hugo shortcodes before indexing")

    encoder = SentenceTransformer(
        settings.embedding_model,
        device="cpu",
    )

    token_budget = (
        encoder.max_seq_length
        - encoder.tokenizer.num_special_tokens_to_add(pair=False)
        - 8
    )

    splitter = RecursiveCharacterTextSplitter.from_huggingface_tokenizer(
        tokenizer=encoder.tokenizer,
        chunk_size=token_budget,
        chunk_overlap=40,
        separators=["\n\n", "\n", " ", ""],
        add_start_index=True,
    )

    chunks = splitter.split_documents([document])

    for index, chunk in enumerate(chunks):
        metadata = chunk.metadata

        metadata["chunk_index"] = index
        metadata["chunk_id"] = (
            f"{metadata['document_id']}:"
            f"v{metadata['version']}:chunk-{index:04d}"
        )
        metadata["chunk_size_chars"] = len(chunk.page_content)
        metadata["chunking_method"] = "embedding_tokenizer"
        metadata["chunk_token_budget"] = token_budget

    print(f"Documents: 1")
    print(f"Chunks: {len(chunks)}")
    print(f"Token budget: {token_budget}")

    del encoder

    indexed_count = index_chunks(chunks)

    print(f"OK: Indexed {indexed_count} Kubernetes chunks.")


if __name__ == "__main__":
    main()