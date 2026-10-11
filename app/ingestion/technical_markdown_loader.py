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


def clean_hugo_markdown(
    content: str,
    code_samples: dict[str, str],
    feature_states: dict[str, str],
) -> tuple[str, list[str]]:
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

        if name.lstrip("/") in {"note", "warning", "caution"}:
            return "\n"

        if name in {"tabs", "/tabs", "/tab"}:
            return "\n"

        if name == "tab":
            return f"\n### {attributes.get('name', 'Example')}\n"

        if name == "heading":
            if '"whatsnext"' in expression:
                return "\n## What's next\n"

        if name == "api-reference":
            page = attributes.get("page")

            if page:
                return (
                    "\nAPI reference: "
                    f"https://kubernetes.io/docs/reference/"
                    f"kubernetes-api/{page}/\n"
                )

        if name == "code_sample":
            sample_path = attributes.get("file")

            if sample_path in code_samples:
                sample = code_samples[sample_path].rstrip()
                return f"\n```yaml\n{sample}\n```\n"

        if name == "feature-state":
            feature_name = attributes.get("feature_gate_name")

            if feature_name in feature_states:
                return f"\n{feature_states[feature_name]}\n"

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
    sample_path = markdown_path.parent / "nginx-deployment.yaml"

    code_samples = {}

    if sample_path.is_file():
        sample_bytes = sample_path.read_bytes()

        code_samples["controllers/nginx-deployment.yaml"] = (
            sample_bytes.decode("utf-8-sig")
        )

        metadata["code_sample_sha256"] = hashlib.sha256(
            sample_bytes
        ).hexdigest()

    feature_states = {}
    feature_path = (
        markdown_path.parent
        / "DeploymentReplicaSetTerminatingReplicas.md"
    )

    if feature_path.is_file():
        feature_bytes = feature_path.read_bytes()
        feature_post = frontmatter.loads(
            feature_bytes.decode("utf-8-sig")
        )

        feature_name = feature_post.metadata["title"]
        stage_lines = []

        for stage in feature_post.metadata["stages"]:
            enabled = stage["defaultValue"]

            if not isinstance(enabled, bool):
                raise ValueError("Feature defaultValue must be boolean")

            start_version = str(stage["fromVersion"])
            end_version = stage.get("toVersion")

            version_range = (
                f"Kubernetes {start_version} through {end_version}"
                if end_version is not None
                else f"Kubernetes {start_version} onward in this snapshot"
            )

            stage_lines.append(
                f"- {version_range}: {stage['stage']}; "
                f"enabled by default: {str(enabled).lower()}."
            )

        feature_states[feature_name] = (
            f"Feature gate: {feature_name}\n"
            + "\n".join(stage_lines)
            + "\n"
            + feature_post.content.strip()
        )

        metadata["feature_gate_sha256"] = hashlib.sha256(
            feature_bytes
        ).hexdigest()

    content, unresolved = clean_hugo_markdown(
        post.content,
        code_samples=code_samples,
        feature_states=feature_states,
    )

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