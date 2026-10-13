import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVALUATION = ROOT / "evaluation"

CONFIGS = [
    (
        "nist",
        "nist_dev_rubric_v1.json",
        "nist_dev_evidence_v2.jsonl",
        "nist_dev_run2",
    ),
    (
        "kubernetes",
        "kubernetes_dev_rubric_v1.json",
        "kubernetes_dev_evidence_v1.jsonl",
        "kubernetes_dev_run1",
    ),
]

MODELS = ["phi4-mini", "qwen3", "deepseek", "gemma4"]


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_jsonl(path):
    rows = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8-sig").splitlines()
        if line.strip()
    ]
    ids = [row["question_id"] for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError(f"Duplicate question IDs: {path.name}")
    return {row["question_id"]: row for row in rows}


def main():
    output = EVALUATION / "scores" / "manual_reviews_v1.json"

    if output.exists():
        raise FileExistsError(
            "Output already exists. Keep the existing manual reviews."
        )

    reviews = []

    for dataset, rubric_name, evidence_name, suffix in CONFIGS:
        rubric = read_json(EVALUATION / "rubrics" / rubric_name)
        evidence = read_jsonl(EVALUATION / "datasets" / evidence_name)
        expected_ids = {question["id"] for question in rubric}

        if set(evidence) != expected_ids:
            raise ValueError(f"Evidence IDs do not match: {dataset}")

        for model in MODELS:
            result_name = f"{model}_{suffix}.jsonl"
            results = read_jsonl(EVALUATION / "results" / result_name)

            if set(results) != expected_ids:
                raise ValueError(f"Result IDs do not match: {result_name}")

            for question in rubric:
                question_id = question["id"]
                result = results[question_id]

                reviews.append({
                    "dataset": dataset,
                    "rubric_file": rubric_name,
                    "evidence_file": evidence_name,
                    "result_file": result_name,
                    "question_id": question_id,
                    "question": question["question"],
                    "answerable": question["answerable"],
                    "answer": result["answer"],
                    "generation_seconds": result["generation_seconds"],
                    "run_status": result["status"],
                    "required_facts": question["required_facts"],
                    "required_fact_scores": [
                        None for _ in question["required_facts"]
                    ],
                    "unsupported_claims": None,
                    "refusal": None,
                    "claims": None,
                    "format_pass": None,
                    "review_status": "pending",
                    "notes": "",
                })

    output.parent.mkdir(parents=True, exist_ok=True)

    with output.open("x", encoding="utf-8") as file:
        json.dump(
            {"schema_version": 1, "reviews": reviews},
            file,
            ensure_ascii=False,
            indent=2,
        )
        file.write("\n")

    print(f"Created {len(reviews)} pending reviews.")
    print(output)


if __name__ == "__main__":
    main()