import hashlib
import json
from pathlib import Path

from app.config import settings
from app.retrieval.retriever import DocumentRetriever

import argparse

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Freeze retrieved evidence for an evaluation dataset"
    )
    parser.add_argument("--dataset", default="rag_dev.json")
    parser.add_argument("--output", default="rag_dev_evidence.jsonl")
    parser.add_argument("--top-k", type=int, default=3)
    args = parser.parse_args()

    if args.top_k < 1:
        parser.error("--top-k must be at least 1")

    project_root = Path(__file__).resolve().parents[1]
    datasets_dir = (
        project_root / "evaluation" / "datasets"
    ).resolve()

    dataset_path = (datasets_dir / args.dataset).resolve()
    output_path = (datasets_dir / args.output).resolve()

    for path in (dataset_path, output_path):
        if not path.is_relative_to(datasets_dir):
            raise ValueError(
                "Dataset and evidence must be inside evaluation/datasets"
            )

    if dataset_path == output_path:
        raise ValueError("Dataset and output must be different files")

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
            "U  se a new filename if you want a new evidence snapshot."
        )

    retriever = DocumentRetriever()
    records = []

    try:
        for item in questions:
            question = item["question"]
            results = retriever.retrieve(
                question,
                top_k=args.top_k,
            )

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
                "top_k": args.top_k,
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