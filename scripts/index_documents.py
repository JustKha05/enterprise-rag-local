from pathlib import Path

from app.ingestion.chunker import split_documents
from app.ingestion.indexer import index_chunks
from app.ingestion.markdown_loader import load_markdown_documents


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]

    documents = load_markdown_documents(
        directory=project_root / "data" / "raw" / "synthetic",
        project_root=project_root,
    )

    chunks = split_documents(
        documents,
        chunk_size=600,
        chunk_overlap=100,
    )

    print(f"Documents: {len(documents)}")
    print(f"Chunks: {len(chunks)}")

    indexed_count = index_chunks(chunks)

    print(f"OK: Indexed {indexed_count} chunks into Qdrant.")


if __name__ == "__main__":
    main()