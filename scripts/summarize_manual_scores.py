"""Aggregate explicit reviewer annotations; never infer scores from answer text."""
import argparse
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean, median


def ratio(numerator, denominator):
    return None if denominator == 0 else numerator / denominator


def summarize(data):
    groups = defaultdict(list)
    seen = set()
    for row in data['reviews']:
        key = (row['dataset'], row['result_file'], row['question_id'])
        if key in seen:
            raise ValueError(f'Duplicate review: {key}')
        seen.add(key)
        if row['review_status'] != 'completed':
            raise ValueError(f'Unreviewed entry: {key}')
        facts = row['required_fact_scores']
        if len(facts) != len(row['required_facts']) or any(type(x) is not int or x not in (0, 1) for x in facts):
            raise ValueError(f'Invalid fact scores: {key}')
        if not isinstance(row['claims'], list) or not isinstance(row['unsupported_claims'], list):
            raise ValueError(f'Missing claim annotations: {key}')
        if type(row['format_pass']) is not bool or row['refusal'] not in {'none', 'correct', 'incorrect', 'mixed'}:
            raise ValueError(f'Invalid review annotations: {key}')
        for claim in row['claims']:
            checks = claim['citation_checks']
            if [x['source_label'] for x in checks] != claim['citations']:
                raise ValueError(f'Citation checks mismatch: {key}')
            if any(type(x['supported']) is not bool for x in checks):
                raise ValueError(f'Invalid citation support: {key}')
            if claim['supported_by_citations'] != any(x['supported'] for x in checks):
                raise ValueError(f'Coverage mismatch: {key}')
        groups[(row['dataset'], row['result_file'])].append(row)
    output = []
    for (dataset, result_file), rows in sorted(groups.items()):
        # Six questions are required for these explicitly scoped development runs.
        expected = {f'{"NIST" if dataset == "nist" else "K8S"}-Q{i:02}' for i in range(1, 7)}
        if {r['question_id'] for r in rows} != expected:
            raise ValueError(f'Incomplete question set: {result_file}')
        answerable = [r for r in rows if r['answerable']]
        unanswerable = [r for r in rows if not r['answerable']]
        correct = sum(
            r['run_status'] == 'completed' and not r['unsupported_claims'] and (
                (r['answerable'] and all(r['required_fact_scores']) and r['refusal'] == 'none')
                or (not r['answerable'] and r['refusal'] == 'correct' and not r['claims'])
            ) for r in rows
        )
        facts = [v for r in answerable for v in r['required_fact_scores']]
        claims = [c for r in rows for c in r['claims']]
        links = [x for c in claims for x in c['citation_checks']]
        durations = [r['generation_seconds'] for r in rows]
        counts = {
            'questions': len(rows), 'correct_answers': correct,
            'required_facts': len(facts), 'correct_required_facts': sum(facts),
            'citation_links': len(links), 'supported_citation_links': sum(x['supported'] for x in links),
            'claims': len(claims), 'citation_covered_claims': sum(c['supported_by_citations'] for c in claims),
            'answerable_questions': len(answerable),
            'false_refusals': sum(r['refusal'] in {'incorrect', 'mixed'} for r in answerable),
            'unanswerable_questions': len(unanswerable),
            'correct_refusals': sum(r['refusal'] == 'correct' and not r['claims'] for r in unanswerable),
            'format_passes': sum(r['format_pass'] for r in rows),
        }
        output.append({
            'dataset': dataset, 'result_file': result_file, 'counts': counts,
            'answer_accuracy': ratio(correct, len(rows)),
            'required_fact_coverage_micro': ratio(sum(facts), len(facts)),
            'citation_precision_micro': ratio(counts['supported_citation_links'], len(links)),
            'citation_coverage_micro': ratio(counts['citation_covered_claims'], len(claims)),
            'correct_refusal_rate': ratio(counts['correct_refusals'], len(unanswerable)),
            'false_refusal_rate': ratio(counts['false_refusals'], len(answerable)),
            'format_compliance': ratio(counts['format_passes'], len(rows)),
            'latency_seconds': {'mean': mean(durations), 'median': median(durations),
                                'min': min(durations), 'max': max(durations), 'total': sum(durations)},
        })
    return output


def markdown(rows):
    def pct(x):
        return 'N/A' if x is None else f'{x * 100:.1f}%'
    lines = ['# Assistant-reviewed development results', '',
             'Not yet human-verified. Six questions per dataset/model; five answerable and one unanswerable.', '',
             '| Dataset | Model | Answer accuracy | Required facts | Citation precision | Citation coverage | Correct refusal | False refusal | Mean latency |',
             '|---|---|---:|---:|---:|---:|---:|---:|---:|']
    for r in rows:
        model = r['result_file'].split('_')[0]
        counts = r['counts']
        lines.append(f"| {r['dataset']} | {model} | {counts['correct_answers']}/6 ({pct(r['answer_accuracy'])}) | {counts['correct_required_facts']}/{counts['required_facts']} | {pct(r['citation_precision_micro'])} | {pct(r['citation_coverage_micro'])} | {counts['correct_refusals']}/{counts['unanswerable_questions']} | {counts['false_refusals']}/{counts['answerable_questions']} | {r['latency_seconds']['mean']:.2f}s |")
    lines += ['', 'Citation metrics are micro-averages over annotated atomic claims and claim-source links. Refusal-only outputs add no claims to citation denominators; false refusals are scored separately.', '',
              'NIST v2 uses top-k=6; Kubernetes v1 uses top-k=3. Prompt versions may differ across datasets. DeepSeek uses reasoning and a larger output budget. Latency includes prompt processing and generation, including model loading when applicable.', '',
              'Strict NIST Q04 fact 2 requires practices/controls guidance. Generic online-resources mentions do not pass this fact. Kubernetes Q05 is rescored with a corrected complete-state and zero-replica rubric.', '',
              'Retrieval Recall@k, Precision@k, MRR and NDCG are not reported because exhaustive relevance labels have not been created.']
    return '\n'.join(lines) + '\n'


def main():
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, default=root/'evaluation/scores/manual_reviews_assistant_v1.json')
    parser.add_argument('--output-dir', type=Path, default=root/'evaluation/reports/assistant_v1')
    args = parser.parse_args()
    data = json.loads(args.input.read_text(encoding='utf-8-sig'))
    rows = summarize(data)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    targets = [args.output_dir/'metrics.json', args.output_dir/'benchmark.md']
    if any(p.exists() for p in targets):
        raise FileExistsError('Reports exist. Choose a new output directory to preserve previous results.')
    targets[0].write_text(json.dumps({'review_method': data.get('review_method'), 'results': rows}, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    targets[1].write_text(markdown(rows), encoding='utf-8')
    print(targets[1].read_text(encoding='utf-8'))


if __name__ == '__main__':
    main()
