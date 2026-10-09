from pathlib import Path

from app.ingestion.technical_markdown_loader import (
    load_technical_markdown,
)


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    source_dir = project_root / "data" / "raw" / "kubernetes"

    document = load_technical_markdown(
        markdown_path=source_dir / "deployment.md",
        metadata_path=source_dir / "deployment.metadata.json",
        project_root=project_root,
    )

    print(f"Title: {document.metadata['title']}")
    print(f"Source URL: {document.metadata['source_url']}")
    print(f"Content length: {len(document.page_content)} characters")

    print("\nPreview:")
    print(document.page_content[:1200])

    unresolved = document.metadata["unresolved_shortcodes"]
    print(f"\nUnresolved shortcodes: {len(unresolved)}")

    for expression in sorted(set(unresolved)):
        print(f"  {expression}")

    command = "kubectl rollout undo deployment/nginx-deployment"
    position = document.page_content.find(command)

    if position == -1:
        raise SystemExit("ERROR: Rollback command is missing")

    print("\nRollback excerpt:")
    print(
        document.page_content[
            max(0, position - 200):position + 500
        ]
    )

    print("\nOK: Kubernetes Markdown loaded.")
    if unresolved:
        print("Review unresolved shortcodes before indexing.")


if __name__ == "__main__":
    main()