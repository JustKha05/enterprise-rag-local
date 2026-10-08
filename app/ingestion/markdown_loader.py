from pathlib import Path

import frontmatter
from langchain_core.documents import Document


REQUIRED_METADATA = (
    "document_id",
    "title",
    "department",
    "document_type",
    "version",
    "status",
    "effective_date",
    "source_type",
    "language",
)


def load_markdown_documents(
    directory: Path,
    project_root: Path,
) -> list[Document]:
    directory = directory.resolve()
    project_root = project_root.resolve()

    if not directory.is_dir():
        raise FileNotFoundError(
            f"Document directory does not exist: {directory}"
        )

    paths = sorted(directory.rglob("*.md"))

    if not paths:
        raise ValueError(f"No Markdown files found in: {directory}")

    documents = []
    seen_versions = set()

    for path in paths:
        raw_text = path.read_text(encoding="utf-8-sig")
        post = frontmatter.loads(raw_text)

        metadata = dict(post.metadata)
        content = post.content.strip()

        invalid_fields = [
            field
            for field in REQUIRED_METADATA
            if not isinstance(metadata.get(field), str)
            or not metadata[field].strip()
        ]

        if invalid_fields:
            raise ValueError(
                f"{path.name}: missing, empty, or non-string metadata: "
                f"{', '.join(invalid_fields)}"
            )

        if not content:
            raise ValueError(f"{path.name}: document content is empty")

        version_key = (
            metadata["document_id"],
            metadata["version"],
        )

        if version_key in seen_versions:
            raise ValueError(
                f"{path.name}: duplicate document ID and version: "
                f"{version_key}"
            )

        seen_versions.add(version_key)

        metadata["source"] = path.relative_to(
            project_root
        ).as_posix()

        documents.append(
            Document(
                page_content=content,
                metadata=metadata,
            )
        )

    return documents