import hashlib
import json
from pathlib import Path

from app.config import settings
from app.retrieval.retriever import DocumentRetriever


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]

    dataset_path = (
        project_root / "evaluation" / "datasets" / "rag_dev.json"
    )
    output_path = (
        project_root / "evaluation" / "datasets" / "rag_dev_evidence.jsonl"
    )

    dataset_bytes = dataset_path.read_bytes()
    questions = json.loads(dataset_bytes.decode("utf-8-sig"))
    dataset_hash = hashlib.sha256(dataset_bytes).hexdigest()

    if not questions:
        raise ValueError("The evaluation dataset is empty")

    question_ids = [item["id"] for item in questions]

    if len(question_ids) != len(set(question_ids)):
        raise ValueError("Duplicate question IDs")

    if output_path.exists():
        raise FileExistsError(
            f"Evidence already exists: {output_path}\n"
            "Use a new filename if you want a new evidence snapshot."
        )

    retriever = DocumentRetriever()
    records = []

    try:
        for item in questions:
            question = item["question"]
            results = retriever.retrieve(question, top_k=3)

            if not results:
                raise ValueError(
                    f"{item['id']}: no evidence was retrieved"
                )

            sources = []

            for index, result in enumerate(results, start=1):
                sources.append(
                    {
                        "label": f"S{index}",
                        "score": result.score,
                        "page_content": result.document.page_content,
                        "metadata": result.document.metadata,
                    }
                )

            record = {
                "question_id": item["id"],
                "question": question,
                "dataset_sha256": dataset_hash,
                "collection_name": settings.collection_name,
                "embedding_model": settings.embedding_model,
                "top_k": 3,
                "sources": sources,
            }

            records.append(record)

            source_ids = [
                source["metadata"]["document_id"]
                for source in sources
            ]

            print(f"{item['id']}: {', '.join(source_ids)}")

    finally:
        retriever.close()

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("x", encoding="utf-8") as output:
        for record in records:
            output.write(
                json.dumps(record, ensure_ascii=False) + "\n"
            )

    print()
    print(f"OK: Saved evidence for {len(records)} questions.")
    print(f"Output: {output_path}")


if __name__ == "__main__":
    main()