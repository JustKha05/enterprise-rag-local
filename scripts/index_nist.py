from pathlib import Path

from app.config import settings
from app.ingestion.indexer import index_chunks
from app.ingestion.pdf_loader import load_pdf_documents

from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer

NIST_COLLECTION = "nist_csf2_minilm_v1"


def main() -> None:
    if settings.collection_name != NIST_COLLECTION:
        raise SystemExit(
            f"ERROR: Set QDRANT_COLLECTION to {NIST_COLLECTION} "
            "before running this script."
        )

    project_root = Path(__file__).resolve().parents[1]
    source_dir = project_root / "data" / "raw" / "nist"

    documents = load_pdf_documents(
        pdf_path=source_dir / "NIST.CSWP.29.pdf",
        metadata_path=source_dir / "NIST.CSWP.29.metadata.json",
        project_root=project_root,
    )

    encoder = SentenceTransformer(
        settings.embedding_model,
        device="cpu",
    )

    # Leave room for the tokenizer's special tokens.
    token_budget = (
        encoder.max_seq_length
        - encoder.tokenizer.num_special_tokens_to_add(pair=False)
        - 8
    )

    splitter = RecursiveCharacterTextSplitter.from_huggingface_tokenizer(
        tokenizer=encoder.tokenizer,
        chunk_size=token_budget,
        chunk_overlap=40,
        separators=["\n\n", "\n", " ", ""],
        add_start_index=True,
    )

    chunks = splitter.split_documents(documents)

    for index, chunk in enumerate(chunks):
        metadata = chunk.metadata

        metadata["chunk_index"] = index
        metadata["chunk_id"] = (
            f"{metadata['document_id']}:"
            f"v{metadata['version']}:chunk-{index:04d}"
        )
        metadata["chunk_size_chars"] = len(chunk.page_content)
        metadata["chunking_method"] = "embedding_tokenizer"
        metadata["chunk_token_budget"] = token_budget

    # Release this model before index_chunks loads its encoder.
    del encoder

    print(f"Pages with text: {len(documents)}")
    print(f"Chunks: {len(chunks)}")

    for chunk in chunks[:3]:
        print()
        print(f"Chunk: {chunk.metadata['chunk_id']}")
        print(f"PDF page: {chunk.metadata['pdf_page']}")
        print(chunk.page_content[:300])

    indexed_count = index_chunks(chunks)

    print()
    print(f"OK: Indexed {indexed_count} NIST chunks.")


if __name__ == "__main__":
    main()