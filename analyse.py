"""Reproduce the SAF H1 2026 June-exclusion diagnostic using public aggregates only.
Python 3, standard library. Run: python3 analyse.py
No attempt is made to recover missing sales, recompute medians, or infer student use.
"""
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
source = ROOT / 'database-evidence.json'
data = json.loads(source.read_text())
towns = data['sold']['cities']
assert len(towns) == 8
assert len({t['town'] for t in towns}) == 8
assert all([m['month'] for m in t['monthly_observed_sales']] ==
           [f'2026-{m:02d}' for m in range(1, 7)] for t in towns)
assert all(sum(m['sales'] for m in t['monthly_observed_sales']) == t['observed_sales_h1'] for t in towns)
total = sum(t['observed_sales_h1'] for t in towns)
june = sum(t['monthly_observed_sales'][5]['sales'] for t in towns)
assert total == data['sold']['observedRecordCount'] == 19871
retained = total - june
rows = []
for t in towns:
    n = t['observed_sales_h1']
    j = t['monthly_observed_sales'][5]['sales']
    rows.append(dict(town=t['town'], h1_count=n, june_count=j,
        jan_may_count=n-j, june_share_pct=100*j/n,
        h1_sample_share_pct=100*n/total,
        jan_may_sample_share_pct=100*(n-j)/retained,
        share_change_pp=100*((n-j)/retained - n/total)))
assert sum(r['jan_may_count'] for r in rows) == retained
assert abs(sum(r['share_change_pp'] for r in rows)) < 1e-10
h1_order = [r['town'] for r in sorted(rows, key=lambda r:r['h1_count'], reverse=True)]
retained_order = [r['town'] for r in sorted(rows, key=lambda r:r['jan_may_count'], reverse=True)]
summary = dict(research_id='SAF-H1-2026', analysis_date='2026-11-02',
    source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
    source_compilation_date=data['compilationDate'], h1_count=total,
    june_count=june, jan_may_count=retained, june_share_pct=100*june/total,
    maximum_absolute_share_change_pp=max(abs(r['share_change_pp']) for r in rows),
    h1_count_ranking=h1_order, jan_may_count_ranking=retained_order,
    report_url='https://studentaccommodationfinance.co.uk/insights/h1-2026-student-accommodation-finance-report/',
    limits='General residential transactions in eight exact postal towns; fixed 6 August 2026 source file. Excluding June is a sensitivity check, not a correction for registration lag. No pooled or January-May price medians can be recovered from these aggregates.')
with (ROOT/'town-sensitivity.csv').open('w', newline='') as f:
    w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
(ROOT/'results.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary, indent=2))
