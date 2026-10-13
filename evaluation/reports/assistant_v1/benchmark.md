# Assistant-reviewed development results

Not yet human-verified. Six questions per dataset/model; five answerable and one unanswerable.

| Dataset | Model | Answer accuracy | Required facts | Citation precision | Citation coverage | Correct refusal | False refusal | Mean latency |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| kubernetes | deepseek | 3/6 (50.0%) | 4/8 | 75.0% | 83.3% | 1/1 | 0/5 | 175.59s |
| kubernetes | gemma4 | 5/6 (83.3%) | 7/8 | 100.0% | 100.0% | 1/1 | 0/5 | 244.44s |
| kubernetes | phi4-mini | 4/6 (66.7%) | 5/8 | 83.3% | 71.4% | 1/1 | 1/5 | 35.23s |
| kubernetes | qwen3 | 4/6 (66.7%) | 7/8 | 94.1% | 88.9% | 1/1 | 0/5 | 86.82s |
| nist | deepseek | 4/6 (66.7%) | 14/16 | 88.5% | 100.0% | 1/1 | 0/5 | 290.17s |
| nist | gemma4 | 5/6 (83.3%) | 15/16 | 92.3% | 95.7% | 1/1 | 0/5 | 399.30s |
| nist | phi4-mini | 4/6 (66.7%) | 14/16 | 65.0% | 81.2% | 1/1 | 1/5 | 87.72s |
| nist | qwen3 | 5/6 (83.3%) | 15/16 | 94.7% | 90.0% | 1/1 | 0/5 | 191.38s |

Citation metrics are micro-averages over annotated atomic claims and claim-source links. Refusal-only outputs add no claims to citation denominators; false refusals are scored separately.

NIST v2 uses top-k=6; Kubernetes v1 uses top-k=3. Prompt versions may differ across datasets. DeepSeek uses reasoning and a larger output budget. Latency includes prompt processing and generation, including model loading when applicable.

Strict NIST Q04 fact 2 requires practices/controls guidance. Generic online-resources mentions do not pass this fact. Kubernetes Q05 is rescored with a corrected complete-state and zero-replica rubric.

Retrieval Recall@k, Precision@k, MRR and NDCG are not reported because exhaustive relevance labels have not been created.
