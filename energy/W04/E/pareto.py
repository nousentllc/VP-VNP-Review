"""Descriptive per-scenario dominance on three physical outcomes from validated metrics."""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TOLERANCE = 1e-6

def classify(delta):
    if all(abs(x) <= TOLERANCE for x in delta):
        return 'equivalent'
    if all(x <= TOLERANCE for x in delta):
        return 'first_dominates'
    if all(x >= -TOLERANCE for x in delta):
        return 'second_dominates'
    return 'tradeoff'

def run(metrics=ROOT/'results/scenario_metrics.csv', output_path=ROOT/'results/pareto.csv'):
    with metrics.open() as f:
        records = {(r['case'], r['policy']): r for r in csv.DictReader(f)}
    contrasts = [('value6','none6'),('value6','rule6'),('none6','legacy6'),
                 ('value12','none12'),('value12','rule12'),('value12','value6'),
                 ('value3','none3'),('value3','rule3')]
    header = ['arm','reference','regime','cases','first_dominates','second_dominates','equivalent','tradeoff']
    with output_path.open('w',newline='') as f:
        writer = csv.DictWriter(f,header)
        writer.writeheader()
        for arm,ref in contrasts:
            for reg in ('all','base','outage_reserve','biased_forecast'):
                counters = {k: 0 for k in header[4:]}
                for (case,pol),row in records.items():
                    if pol != arm or reg not in ('all',row['regime']):
                        continue
                    diff = [float(row[k])-float(records[case,ref][k]) for k in ('unserved','losses','throughput')]
                    counters[classify(diff)] += 1
                writer.writerow(dict(arm=arm,reference=ref,regime=reg,cases=sum(counters.values()),**counters))

if __name__ == '__main__':
    run()
