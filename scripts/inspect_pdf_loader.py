from pathlib import Path

from app.ingestion.pdf_loader import load_pdf_documents


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    source_dir = project_root / "data" / "raw" / "nist"

    documents = load_pdf_documents(
        pdf_path=source_dir / "NIST.CSWP.29.pdf",
        metadata_path=source_dir / "NIST.CSWP.29.metadata.json",
        project_root=project_root,
    )

    print(f"Pages with extracted text: {len(documents)}")
    print(f"Total PDF pages: {documents[0].metadata['total_pdf_pages']}")

    for document in documents:
        print(
            f"PDF page {document.metadata['pdf_page']:02d}: "
            f"{len(document.page_content)} characters"
        )

    # Preview pages from the beginning, middle, and end.
    sample_indexes = sorted(
        {0, len(documents) // 2, len(documents) - 1}
    )

    for index in sample_indexes:
        document = documents[index]

        print()
        print(f"Preview: PDF page {document.metadata['pdf_page']}")
        print(document.page_content[:1500])

    print()
    print("OK: PDF pages loaded with source metadata.")


if __name__ == "__main__":
    main()