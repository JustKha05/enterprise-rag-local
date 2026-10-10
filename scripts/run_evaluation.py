import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama

from app.config import settings
from app.rag.prompts import SYSTEM_PROMPT, build_user_prompt


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate a model using frozen evidence"
    )
    parser.add_argument("--model", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument(
        "--evidence",
        default="rag_dev_evidence.jsonl",
    )
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parents[1]
    datasets_dir = (
        project_root / "evaluation" / "datasets"
    ).resolve()

    evidence_path = (datasets_dir / args.evidence).resolve()

    if not evidence_path.is_relative_to(datasets_dir):
        raise ValueError(
            "Evidence must be inside evaluation/datasets"
        )

    output_path = (
        project_root / "evaluation" / "results" / args.output
    ).resolve()

    results_dir = (
        project_root / "evaluation" / "results"
    ).resolve()

    if not output_path.is_relative_to(results_dir):
        raise ValueError("Output must be inside evaluation/results")

    if output_path.exists():
        raise FileExistsError(
            f"Output already exists: {output_path}. "
            "Choose a new filename."
        )

    evidence_bytes = evidence_path.read_bytes()
    evidence_hash = hashlib.sha256(evidence_bytes).hexdigest()
    prompt_hash = hashlib.sha256(
        SYSTEM_PROMPT.encode("utf-8")
    ).hexdigest()

    cases = [
        json.loads(line)
        for line in evidence_bytes.decode("utf-8-sig").splitlines()
        if line.strip()
    ]

    if not cases:
        raise ValueError("Evidence file is empty")

    family = args.model.split(":")[0]
    reasoning = None
    output_limit = 400

    if family in {"qwen3", "gemma4"}:
        reasoning = False
    elif family == "deepseek-r1":
        reasoning = True
        output_limit = 1200

    model_options = {}
    if reasoning is not None:
        model_options["reasoning"] = reasoning

    llm = ChatOllama(
        model=args.model,
        base_url=settings.ollama_url,
        temperature=0,
        num_ctx=4096,
        num_predict=output_limit,
        keep_alive="5m",
        client_kwargs={"timeout": 600.0},
        **model_options,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("x", encoding="utf-8") as output:
        for index, case in enumerate(cases, start=1):
            user_prompt = build_user_prompt(
                case["question"],
                case["sources"],
            )

            print(
                f"[{index}/{len(cases)}] "
                f"{args.model}: {case['question_id']}",
                flush=True,
            )

            record = {
                "question_id": case["question_id"],
                "question": case["question"],
                "requested_model": args.model,
                "timestamp_utc": datetime.now(
                    timezone.utc
                ).isoformat(),
                "evidence_sha256": evidence_hash,
                "system_prompt_sha256": prompt_hash,
                "configuration": {
                    "temperature": 0,
                    "num_ctx": 4096,
                    "num_predict": output_limit,
                    "reasoning": reasoning,
                },
                "messages_sha256": hashlib.sha256(
                    json.dumps(
                        [
                            {
                                "role": "system",
                                "content": SYSTEM_PROMPT,
                            },
                            {
                                "role": "user",
                                "content": user_prompt,
                            },
                        ],
                        ensure_ascii=False,
                        sort_keys=True,
                    ).encode("utf-8")
                ).hexdigest(),
            }

            start = perf_counter()

            try:
                message = llm.invoke(
                    [
                        SystemMessage(content=SYSTEM_PROMPT),
                        HumanMessage(content=user_prompt),
                    ]
                )

                record["generation_seconds"] = (
                    perf_counter() - start
                )

                if not isinstance(message.content, str):
                    raise TypeError("Expected a text answer")

                metadata = message.response_metadata
                answer = message.content.strip()
                response_model = metadata.get("model")
                done_reason = metadata.get("done_reason")

                if response_model != args.model:
                    raise ValueError(
                        f"Response model mismatch: {response_model}"
                    )

                record.update(
                    {
                        "status": (
                            "empty_answer"
                            if not answer
                            else "truncated"
                            if done_reason == "length"
                            else "completed"
                        ),
                        "answer": answer,
                        "response_metadata": metadata,
                        "usage_metadata": message.usage_metadata,
                        "reasoning_returned": bool(
                            message.additional_kwargs.get(
                                "reasoning_content"
                            )
                        ),
                    }
                )

            except Exception as exc:
                record.update(
                    {
                        "status": "error",
                        "generation_seconds": perf_counter() - start,
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                    }
                )

            output.write(
                json.dumps(record, ensure_ascii=False) + "\n"
            )
            output.flush()

            print(
                f"  {record['status']} "
                f"({record['generation_seconds']:.2f}s)",
                flush=True,
            )

    print(f"Saved results: {output_path}")


if __name__ == "__main__":
    main()