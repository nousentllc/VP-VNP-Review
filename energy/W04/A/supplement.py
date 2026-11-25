"""Stratify by observed raw-LP validation; describe time-specific mechanisms and overruns."""
from pathlib import Path
import argparse,csv,gzip,json
from collections import Counter,defaultdict
import numpy as np


def run(out):
    with gzip.open(out/'trials.jsonl.gz','rt') as f:rows=[json.loads(line) for line in f]
    lookup=defaultdict(list)
    for r in rows:lookup[r['case'],r['arm']].append(r)
    ids=sorted({x['case'] for x in rows})
    admissible={i:all(x['witnesses'][x['stages'][0]['return_witness']]['valid'] for x in lookup[i,'full_lp']
                       if x['stages'][0].get('return_witness') is not None)
                and all('return_witness' in x['stages'][0] for x in lookup[i,'full_lp']) for i in ids}
    classify=defaultdict(list)
    for i in ids:classify['LP admissible' if admissible[i] else 'LP failed admissibility or return'].append(i)
    classify['all']=ids
    size=Counter()
    for i in ids:
        r=lookup[i,'group_start'][0];size[r['n'],r['cohort'],admissible[i]]+=1
    hit_tables={}; quality={};overall={}
    for label,cases in classify.items():
        hit_tables[label]={arm:sum(all(x['target'] is not None for x in lookup[i,arm]) for i in cases)
                           for arm in ['full_lp','full_milp','lp_repair_start','group_start','group_no_transfer']}
        for base in ['full_milp','lp_repair_start','group_no_transfer']:
            metrics={}
            for clock in ['0.05','0.1','0.25','0.5','1.0','2.0']:
                diffs=[];scaled=[];na=0
                for i in cases:
                    def U(p):
                        ys=[x['snapshots'][clock]['U'] for x in lookup[i,p]]
                        return np.median(ys) if all(y is not None for y in ys) else None
                    g,b=U('group_start'),U(base)
                    if b is None or g is None:na+=1;continue
                    d=g-b;diffs.append(d)
                    s=max(1,abs(lookup[i,base][0]['fallback_cost']))
                    scaled.append(d/s)
                diffs=np.array(diffs);scaled=np.array(scaled)
                metrics[clock]=dict(n=len(diffs),missing=na,median_cost_delta=float(np.median(diffs)) if len(diffs) else None,
                    wins=int(sum(scaled < -.001)),ties=int(sum(abs(scaled)<=.001)),losses=int(sum(scaled>.001)),
                    median_normalized_delta=float(np.median(scaled)) if len(scaled) else None)
            quality[label+' / '+base]=metrics
    for arm in ['full_milp','full_lp','lp_repair_start','group_start','group_no_transfer']:
        rs=[x for x in rows if x['arm']==arm]
        elapsed=np.array([x['wall'] for x in rs])
        overall[arm]=dict(p50_wall=float(np.median(elapsed)),p95_wall=float(np.quantile(elapsed,.95)),max_wall=max(elapsed),
                          fallback_only=sum(x['snapshots']['2.0']['source']=='fallback' for x in rs),
                          late_final_stage_returns=sum(w['at']>2 for x in rs for w in x['witnesses']))
    payload=dict(case_strata={k:len(v) for k,v in classify.items()},strata_by_size_cohort=[
        [n,c,a,v] for (n,c,a),v in size.items()],case_hits=hit_tables,group_differences=quality,time_and_fallback=overall)
    (out/'lp_strata.json').write_text(json.dumps(payload,indent=2)+'\n')


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);run(ap.parse_args().out)
