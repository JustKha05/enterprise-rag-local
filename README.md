# Enterprise RAG Assistant

A local document question-answering system with source citations.

## Goals

- Run locally without paid inference APIs.
- Retrieve evidence from a versioned document collection.
- Generate answers with source citations.
- Compare answer quality, latency, and memory usage.

## Generation models

- Phi-4 Mini 3.8B
- Qwen3 8B
- DeepSeek-R1 8B
- Gemma 4 12B

Exact model tags and versions will be recorded during setup.

## Planned data

- Selected official Kubernetes documentation.
- Selected NIST publications.
- Clearly labeled synthetic enterprise documents.

## Approach

Document ingestion -> chunking -> embedding -> Qdrant retrieval
-> local model generation -> evaluation.

The initial project uses pretrained models without fine-tuning.