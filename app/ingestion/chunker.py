from collections import defaultdict

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


def split_documents(
    documents: list[Document],
    chunk_size: int = 600,
    chunk_overlap: int = 100,
) -> list[Document]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero")

    if not 0 <= chunk_overlap < chunk_size:
        raise ValueError(
            "chunk_overlap must be non-negative and smaller than chunk_size"
        )

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", " ", ""],
        add_start_index=True,
    )

    chunks = splitter.split_documents(documents)

    counters = defaultdict(int)

    for chunk in chunks:
        document_id = chunk.metadata["document_id"]
        version = chunk.metadata["version"]
        document_key = (document_id, version)

        chunk_index = counters[document_key]
        counters[document_key] += 1

        chunk.metadata["chunk_index"] = chunk_index
        chunk.metadata["chunk_id"] = (
            f"{document_id}:v{version}:chunk-{chunk_index:04d}"
        )
        chunk.metadata["chunk_size_chars"] = len(chunk.page_content)

    return chunks