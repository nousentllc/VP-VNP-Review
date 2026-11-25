"""Post hoc forecast scoring on held-out issued tails. No controller or calibration changes."""
from collections import defaultdict
import csv
import gzip
import json
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parent


def main(output_path=ROOT/'results/tail_accuracy.csv'):
    groups=defaultdict(list)
    with gzip.open(ROOT/'inputs/holdout.json.gz','rt') as f:
        panel=json.load(f)
    for case in panel['cases']:
        for issue in case['issues']:
            fc=issue['load']
            for lead in range(6,len(fc)):
                actual=case['load'][issue['valid'][lead]]
                e=fc[lead]-actual
                flat=fc[5]-actual
                for regime in ('all',case['regime']):
                    groups[regime].append((e,flat))
    rows=[]
    for regime,obs in groups.items():
        values=np.array(obs)
        for j,name in enumerate(('issued','flat')):
            v=values[:,j]
            rows.append(dict(regime=regime,prediction=name,entries=len(v),
                             mae_MW=np.abs(v).mean(),rmse_MW=np.sqrt((v**2).mean()),mean_error_MW=v.mean()))
    with output_path.open('w',newline='') as f:
        w=csv.DictWriter(f,rows[0].keys());w.writeheader();w.writerows(rows)

if __name__=='__main__':
    main()
