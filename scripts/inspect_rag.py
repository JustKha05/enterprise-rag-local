import argparse

from app.config import settings
from app.rag.pipeline import RAGPipeline


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run a local RAG question-answering check"
    )

    parser.add_argument(
        "--query",
        default="When is a production deployment rollback required?",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=3,
    )

    parser.add_argument(
        "--model",
        default=settings.generation_model,
        help="Ollama model tag to use for generation",
    )

    args = parser.parse_args()

    print(f"Model: {args.model}")
    print("Initializing RAG pipeline...", flush=True)

    pipeline = RAGPipeline(model_name=args.model)

    try:
        print("Retrieving evidence and generating an answer...", flush=True)

        response = pipeline.ask(
            query=args.query,
            top_k=args.top_k,
        )

        print()
        print(f"Question: {args.query}")
        print()
        print("Answer:")
        print(response.answer)

        print()
        print("Retrieved sources:")

        for index, result in enumerate(response.sources, start=1):
            metadata = result.document.metadata

            print(
                f"[S{index}] {metadata['title']} "
                f"(version {metadata['version']})"
            )
            print(f"  Chunk: {metadata['chunk_id']}")
            print(f"  Source: {metadata['source']}")
            print(f"  Retrieval score: {result.score:.4f}")

        print()
        print(f"Retrieval: {response.retrieval_seconds:.2f} seconds")
        print(f"Generation: {response.generation_seconds:.2f} seconds")
        print(f"Done reason: {response.done_reason}")

        if response.done_reason == "length":
            print("WARNING: The answer reached the output token limit.")

    finally:
        pipeline.close()


if __name__ == "__main__":
    main()