"""Descriptive stage attribution, exact controls, and common-bound survival counts."""
import argparse
import csv
import gzip
import json
from collections import Counter
from fractions import Fraction as Q
from pathlib import Path
import statistics
from types import SimpleNamespace

from engine import HERE, ARMS, np, exact_box, round_lower
from audit import exact_replay

def med(xs):
    return float(np.median(xs)) if xs else None

def controls():
    # Independent two-variable integer example. Minimize x + 2y, x+y >= 1, x,y in {0,1}.
    m=SimpleNamespace(cost=[1.,2.],lo=[0.,0.],hi=[1.,1.],lhs=[1.],rhs=[float('inf')],
                      row=[0,0],col=[0,1],val=[1.,1.])
    feasible=[(x,y) for x in [0,1] for y in [0,1] if x+y>=1]
    optimum=min(x+2*y for x,y in feasible)
    for dual in [-10.,0.,.5,1.,2.,4.]:
        assert exact_box(m,[dual])==exact_replay(m,[dual])<=optimum
    assert exact_box(m,[-10.])==0
    assert exact_box(m,[1.])==1
    assert 2>optimum    # Wrong sign in c-A^T y would certify 2 at y=2, real bound equals 1.
    assert exact_box(m,[2.])==1
    assert Q(round_lower(Q(1,10)))<=Q(1,10)<Q(float(Q(1,10)))
    return dict(example='min x+2y, x+y >= 1, x,y binary',full_optimum=optimum,
                checked_multipliers=6,clipped_negative_infinite_side=True,
                wrong_reduced_cost_sign_counterexample=dict(multiplier=2,mutated_lower=2,feasible_cost=1),
                exact_fraction_downward_rounding='1/10')
def run(raw,out):
    with gzip.open(raw,'rt') as f:rows=[json.loads(x) for x in f]
    data=[]
    for arm in ARMS:
        part=[r for r in rows if r['arm']==arm]
        d=dict(arm=arm,trials=len(part));ss=[s for r in part for s in r['stages']]
        for name in ['outer_lp','fixed_sign','partial_sign','native','certificate_lp']:
            stage=[s for s in ss if s['label']==name]
            d[name+'_attempts']=len(stage);d[name+'_statuses']=dict(Counter(s['status'] for s in stage))
            d[name+'_build_median_s']=med([s['build_s'] for s in stage if 'build_s'in s])
            d[name+'_solve_median_s']=med([s['solve_with_callbacks_s'] for s in stage if 'solve_with_callbacks_s'in s])
        d['explicit_outer_then_unrestricted_calls']=sum(any(s['label']=='outer_lp' for s in r['stages']) and
                any(s['label']=='native' and 'solve_with_callbacks_s' in s for s in r['stages']) for r in part)
        d['target_before_any_native_or_repair']=sum(r['target'] is not None and
                all(s['label']=='outer_lp' for s in r['stages']) for r in part)
        d['native_stage_confirmed_starts']=sum(s['label']=='native' and s.get('confirmed_start',False) for s in ss)
        d['native_stage_submitted_starts']=sum(s['label']=='native' and s.get('transfer_api')=='HighsStatus.kOk' for s in ss)
        d['all_stages_presolve_in_log']=sum('presolv' in s.get('log','').lower() for s in ss)
        witness=[w for r in part for w in r['witnesses'] if w['stage']=='outer_lp']
        # A valid LP often appears as a single return checked once; retain all actual witnesses.
        d['raw_lp_return_valid']=sum(w['valid'] for w in witness);d['raw_lp_return_invalid']=sum(not w['valid'] for w in witness)
        cert=[s for s in ss if 'certificate_s' in s]
        d['exact_certificate_median_s']=med([s['certificate_s'] for s in cert])
        d['exact_certificate_p95_s']=float(np.quantile([s['certificate_s'] for s in cert],.95)) if cert else None
        d['exact_cert_by_deadline']=sum(s['certificate_ready']<=2 for s in cert)
        d['dual_time_overrun_certificates']=sum(s['certificate_ready']>2 for s in cert)
        d['checks_and_transfer_median_s']=med([s['transfer_s'] for s in ss if s.get('transfer_s',0)>0])
        d['completes_returned_after_budget']=sum(r['wall']>2 for r in part)
        data.append(d)
    out.mkdir(exist_ok=True,parents=True)
    (out/'mechanisms.json').write_text(json.dumps(dict(stages=data,negative_controls=controls()),indent=2)+'\n')
if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--raw',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();run(a.raw,a.out)
