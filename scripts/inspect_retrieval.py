import argparse

from app.retrieval.retriever import DocumentRetriever


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Inspect retrieved document chunks"
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

    args = parser.parse_args()

    retriever = DocumentRetriever()

    try:
        results = retriever.retrieve(
            query=args.query,
            top_k=args.top_k,
        )

        print(f"Query: {args.query}")
        print(f"Retrieved chunks: {len(results)}")

        for rank, result in enumerate(results, start=1):
            document = result.document
            metadata = document.metadata

            print()
            print(f"Rank: {rank}")
            print(f"Score: {result.score:.4f}")
            print(f"Chunk ID: {metadata['chunk_id']}")
            print(f"Title: {metadata['title']}")
            print(f"Source: {metadata['source']}")
            print("Content:")
            print(document.page_content)

        if not results:
            print("No matching chunks were returned.")
        else:
            print()
            print("OK: Retrieval completed. Check the evidence above.")

    finally:
        retriever.close()


if __name__ == "__main__":
    main()