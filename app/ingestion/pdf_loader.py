import hashlib
import json
from pathlib import Path

from langchain_core.documents import Document
from pypdf import PdfReader


def load_pdf_documents(
    pdf_path: Path,
    metadata_path: Path,
    project_root: Path,
) -> list[Document]:
    metadata = json.loads(
        metadata_path.read_text(encoding="utf-8-sig")
    )

    required_fields = (
        "document_id",
        "title",
        "version",
        "status",
        "source_type",
        "language",
        "source_url",
    )

    for field in required_fields:
        value = metadata.get(field)

        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"Invalid metadata field: {field}")

    file_hash = hashlib.sha256(pdf_path.read_bytes()).hexdigest()

    if file_hash != metadata.get("sha256"):
        raise ValueError("PDF hash does not match source metadata")

    reader = PdfReader(pdf_path)
    documents = []

    for page_number, page in enumerate(reader.pages, start=1):
        content = (page.extract_text() or "").strip()

        if not content:
            print(f"WARNING: No text extracted from PDF page {page_number}")
            continue

        documents.append(
            Document(
                page_content=content,
                metadata={
                    **metadata,
                    "source": pdf_path.resolve().relative_to(
                        project_root.resolve()
                    ).as_posix(),
                    "pdf_page": page_number,
                    "total_pdf_pages": len(reader.pages),
                },
            )
        )

    if not documents:
        raise ValueError("No text was extracted from the PDF")

    return documents