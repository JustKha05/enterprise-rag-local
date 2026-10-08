from collections import Counter
from pathlib import Path

from app.ingestion.chunker import split_documents
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

    counts = Counter(
        (
            chunk.metadata["document_id"],
            chunk.metadata["version"],
        )
        for chunk in chunks
    )

    print(f"Documents: {len(documents)}")
    print(f"Chunks: {len(chunks)}")

    for (document_id, version), count in sorted(counts.items()):
        print(f"{document_id} v{version}: {count} chunks")

    for chunk in chunks:
        metadata = chunk.metadata

        print()
        print(f"Chunk ID: {metadata['chunk_id']}")
        print(f"Source: {metadata['source']}")
        print(f"Start index: {metadata['start_index']}")
        print(f"Length: {metadata['chunk_size_chars']} characters")
        print("Content:")
        print(chunk.page_content)

    if not chunks:
        raise SystemExit("ERROR: No chunks were generated")

    if any(len(chunk.page_content) > 600 for chunk in chunks):
        raise SystemExit("ERROR: A chunk exceeds the size limit")

    chunk_ids = [chunk.metadata["chunk_id"] for chunk in chunks]

    if len(chunk_ids) != len(set(chunk_ids)):
        raise SystemExit("ERROR: Duplicate chunk IDs")

    print()
    print("OK: Chunks generated with source metadata and unique IDs.")


if __name__ == "__main__":
    main()