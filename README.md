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

## Development evaluation

Evaluated four local models on 12 synthetic development questions
using frozen retrieved evidence.

Fully correct answers:
- Phi-4 Mini: 10/12 -> 12/12
- Qwen3 8B: 11/12 -> 11/12
- DeepSeek-R1 8B: 11/12 -> 9/12
- Gemma 4 12B: 12/12 -> 12/12

Known issues:
- Qwen3 confuses approval roles across processes in Q10.
- DeepSeek Q03 reaches the 1200-token limit without a final answer.
- DeepSeek omits an exception in Q04 and a timing trigger in Q06.

These are development results, not an independent test benchmark.
Thinking settings differ across models.