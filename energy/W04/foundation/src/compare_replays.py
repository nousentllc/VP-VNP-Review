"""Compare outcomes under a fresh clock with the frozen reference. Print JSON to stdout."""
import argparse
import gzip
import json
from collections import Counter
from pathlib import Path
from statistics import median
from common import ROOT


def read(p):
    return json.loads(p.read_text())


def compare(first,second):
    result={}
    a,b=([json.loads(line) for line in gzip.open(root/'A/holdout.jsonl.gz','rt')] for root in [first,second])
    key=lambda x:(x['case'],x['policy'],x['repeat'])
    ar,br=({key(row):row for row in rows} for rows in [a,b])
    if set(ar)!=set(br):raise ValueError('A trial keys changed')
    changes=[k for k in ar if (ar[k]['target_time'] is None)!=(br[k]['target_time'] is None)]
    def goals(rows):
        return dict(Counter(q['policy'] for q in rows if q['target_time'] is not None))
    def early(rows):
        cases=sorted({q['case'] for q in rows if q['cohort']=='forced_opposition'})
        faster=[]
        for case in cases:
            times={}
            for method in ['adaptive','full_milp']:
                times[method]=median(next((v['time'] for v in r['events'] if 'upper' in v and v['source']!='fallback'),2.)
                                     for r in rows if r['case']==case and r['policy']==method)
            if times['adaptive']<times['full_milp']:faster.append(case)
        return faster
    result['A']={'trials':len(a),'target_hits_original':goals(a),'target_hits_replay':goals(b),
                 'changed_target_decisions':changes,'forced_cases_with_earlier_first_improvement':[early(a),early(b)],
                 'exact_dual_witnesses_identical':read(first/'A/exact_lp_certificates.json')==read(second/'A/exact_lp_certificates.json'),
                 'raw_lp_validity_changes':sum(ar[k]['steps'][0]['returned_check']['valid']!=br[k]['steps'][0]['returned_check']['valid']
                                                for k in ar if k[1]=='full_lp')}
    result['B']={'checks_identical':read(first/'B/checks.json')==read(second/'B/checks.json'),
                 'axiom_logs_identical':(first/'B/lean-build.log').read_bytes()==(second/'B/lean-build.log').read_bytes()}
    x,y=(read(r/'C/runs.json') for r in [first,second])
    ac=lambda rows:{key(v):v for v in rows}
    x,y=ac(x),ac(y)
    result['C']={'trials':len(x),'max_absolute_cost_difference':max(abs(x[k]['check']['cost']-y[k]['check']['cost']) for k in x),
                 'validity_changes':sum(x[k]['check']['valid']!=y[k]['check']['valid'] for k in x)}
    d=[]
    for f in sorted((first/'D').glob('*.json')):
        x=read(f);y=read(second/'D'/f.name)
        d.append(dict(id=x['id'],on_time=[x['validated_by_deadline'],y['validated_by_deadline']],
                      status=[x['status'],y['status']],
                      costs=[v.get('check',{}).get('objective') for v in [x,y]]))
    result['D']=d
    ea,eb=({(v['case'],v['method']):v for v in read(r/'E/runs.json')} for r in [first,second])
    result['E']={'trials':len(ea),'max_absolute_unserved_difference_MWh':max(abs(v['unserved_MWh']-eb[k]['unserved_MWh']) for k,v in ea.items()),
                 'max_absolute_loss_difference_MWh':max(abs(v['conversion_loss_MWh']-eb[k]['conversion_loss_MWh']) for k,v in ea.items())}
    return result


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('replay',type=Path);ap.add_argument('--reference',type=Path,default=ROOT/'results')
    args=ap.parse_args();print(json.dumps(compare(args.reference,args.replay),indent=2))
