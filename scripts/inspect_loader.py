from pathlib import Path

from app.ingestion.markdown_loader import load_markdown_documents


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    document_dir = project_root / "data" / "raw" / "synthetic"

    documents = load_markdown_documents(
        directory=document_dir,
        project_root=project_root,
    )

    print(f"Loaded documents: {len(documents)}")

    for index, document in enumerate(documents, start=1):
        metadata = document.metadata

        print()
        print(f"Document {index}")
        print(f"ID: {metadata['document_id']}")
        print(f"Title: {metadata['title']}")
        print(f"Version: {metadata['version']}")
        print(f"Source type: {metadata['source_type']}")
        print(f"Source: {metadata['source']}")
        print(f"Content length: {len(document.page_content)} characters")
        print("Preview:")
        print(document.page_content[:200])

    print()
    print("OK: Markdown documents loaded successfully.")


if __name__ == "__main__":
    main()