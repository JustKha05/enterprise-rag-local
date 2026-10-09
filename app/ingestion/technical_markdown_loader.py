import hashlib
import json
import re
from pathlib import Path

import frontmatter
from langchain_core.documents import Document


SHORTCODE_PATTERN = re.compile(
    r"{{[<%]\s*(.*?)\s*[>%]}}",
    flags=re.DOTALL,
)

ATTRIBUTE_PATTERN = re.compile(
    r'([\w-]+)\s*=\s*"([^"]*)"'
)


def clean_hugo_markdown(content: str) -> tuple[str, list[str]]:
    unresolved = []

    def replace_shortcode(match: re.Match) -> str:
        expression = match.group(1).strip()
        name = expression.split()[0] if expression else ""
        attributes = dict(ATTRIBUTE_PATTERN.findall(expression))

        if name == "glossary_tooltip":
            return attributes.get(
                "text",
                attributes.get("term_id", "").replace("-", " "),
            )

        # Remove wrappers while keeping the text between them.
        if name.lstrip("/") in {"note", "warning", "caution"}:
            return "\n"

        # Other shortcodes may insert external content.
        # Keep a visible marker instead of silently deleting them.
        unresolved.append(expression)
        return f"\n[UNRESOLVED HUGO SHORTCODE: {expression}]\n"

    content = re.sub(
        r"<!--.*?-->",
        "",
        content,
        flags=re.DOTALL,
    )
    content = SHORTCODE_PATTERN.sub(replace_shortcode, content)

    return content.strip(), unresolved


def load_technical_markdown(
    markdown_path: Path,
    metadata_path: Path,
    project_root: Path,
) -> Document:
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

    raw_bytes = markdown_path.read_bytes()
    actual_hash = hashlib.sha256(raw_bytes).hexdigest()

    if actual_hash != metadata.get("sha256"):
        raise ValueError("Markdown hash does not match source metadata")

    post = frontmatter.loads(raw_bytes.decode("utf-8-sig"))
    content, unresolved = clean_hugo_markdown(post.content)

    if not content:
        raise ValueError("Document content is empty")

    return Document(
        page_content=content,
        metadata={
            **metadata,
            "source": markdown_path.resolve().relative_to(
                project_root.resolve()
            ).as_posix(),
            "unresolved_shortcodes": unresolved,
        },
    )