"""Recompute W03's frozen 50--2000 ms trajectory comparisons on its archive and fresh replay."""
from collections import defaultdict
from statistics import median
from pathlib import Path
import argparse
import gzip
import json
import zipfile


def summarize(path):
    trials=[json.loads(line) for line in gzip.open(path,'rt')]
    by=defaultdict(list)
    for x in trials:by[x['case'],x['policy']].append(x)
    hits=defaultdict(int)
    for (case,arm),rows in by.items():
        hits[arm]+=int(all(x['target_time'] is not None for x in rows))
    forced=sorted({x['case'] for x in trials if x['cohort']=='forced_opposition'})
    records=[]
    for dt in [.05,.1,.25,.5,1.,2.]:
        r={'seconds':dt}
        for arm in ['full_milp','lp_recovery']:
            def cost(case,policy):
                return median(min(e['upper'] for e in row['events'] if 'upper' in e and
                                  (e['time']<=dt or e['source']=='fallback')) for row in by[case,policy])
            differences=[cost(cid,'adaptive')-cost(cid,arm) for cid in forced]
            r[arm]=dict(better=sum(d< -1e-5 for d in differences),tie=sum(abs(d)<=1e-5 for d in differences),
                        worse=sum(d>1e-5 for d in differences),case_differences=differences)
        records.append(r)
    return dict(trials=len(trials),case_all_three_hit=dict(hits),A_fixed_deadlines=records,case_order=forced)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('archive',type=Path);ap.add_argument('fresh',type=Path)
    ap.add_argument('--reviewer',type=Path);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    rec=dict(historical=summarize(a.archive),fresh=summarize(a.fresh))
    if a.reviewer:
        with zipfile.ZipFile(a.reviewer) as z:prior=json.loads(z.read('audit_w03.json'))
        for key in ['case_all_three_hit','A_fixed_deadlines']:
            if rec['historical'][key]!=prior[key]:raise ValueError('Reviewer mismatch '+key)
        rec['matches_reviewer_fixed_deadlines_and_hit_counts']=True
    a.out.write_text(json.dumps(rec,indent=2)+'\n')
