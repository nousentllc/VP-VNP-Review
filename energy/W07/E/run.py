"""Run in order: freeze inputs; baseline and full-information ceilings; registered comparator; audit."""
from pathlib import Path
import sys
import json
import time
import hashlib
import shutil
import resource
from model import BASE,N,SEEDS,BUDGETS,CALENDARS,START,generate,kernels,powers,price_table,simulate,oracle,save,read
from independent import check
from small import small
import numpy as np

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def freeze(out):
    out.mkdir(parents=True,exist_ok=True)
    design=dict(seeds=SEEDS,budgets=BUDGETS,calendars=CALENDARS,weight_each_seed='1/12',weight_each_calendar_conditional_on_budget='1/4',hours=N)
    save(out/'design.json',design)
    for seed in SEEDS:save(out/'inputs'/f'{seed}.json.gz',generate(seed,3))
    files=sorted((out/'inputs').glob('*.gz'))+[out/'design.json']
    (out/'inputs.sha256').write_text(''.join(f'{sha(f)}  {f.relative_to(out)}\n' for f in files))


def run(out):
    ti=time.perf_counter(); timings={}
    for line in (out/'inputs.sha256').read_text().splitlines():
        dig,name=line.split('  ');assert sha(out/name)==dig
    assert read(out/'design.json')['seeds']==list(SEEDS)
    t=time.perf_counter();v,m=kernels(N,4)
    assert all(v[0,b,START] for b in BUDGETS)
    save(out/'kernels.json.gz',dict(values=v.astype(int).tolist(),actions=m.astype(int).tolist()))
    tiny=[]
    for name,signs,power in [('two_down',[1,1,0],[[2],[2],[2]]),('two_up',[-1,-1,0],[[2],[2],[2]]),
        ('alternating',[1,-1,0],[[2],[1,2],[2]]),('insufficient_recovery',[1,1],[[2],[0]]),
        ('uncertain_outage',[1,1,0],[[0,1,2],[0,1,2],[2]]),('terminal_call',[-1],[[2]])]:
        ks,_=kernels(len(signs),4,signs,power)
        tiny.append(dict(case=name,directions=signs,available=power,root=ks[0].astype(int).tolist()))
    save(out/'small_kernels.json',tiny);timings['kernels_write']=time.perf_counter()-t
    t=time.perf_counter(); inputs={s:read(out/'inputs'/f'{s}.json.gz') for s in SEEDS};cached={}
    for seed,case in inputs.items():cached[seed]=price_table(case,m,(-20,0,20),4)
    timings['baseline_build_all_state_feedback_tables']=time.perf_counter()-t
    gates=[];tp=0.;to=0.;tw=0.
    for seed,case in inputs.items():
        for K in BUDGETS:
            for name,cal in CALENDARS.items():
                start=time.perf_counter();bas=simulate(case,K,cal,cached[seed],K,'robust_three');tp+=time.perf_counter()-start
                start=time.perf_counter();lower,values=oracle(case['actual'],K,cal,m);to+=time.perf_counter()-start
                assert bas['failed'] is None and bas['net_cents']>=lower
                start=time.perf_counter();save(out/'certificates'/f'{seed}_{K}_{name}.json.gz',dict(values=values))
                gates.append(dict(seed=seed,K=K,calendar=name,baseline=bas['net_cents'],oracle=lower,
                    ceiling_cents=bas['net_cents']-lower,excludes_15_per_day=bas['net_cents']-lower<4500))
                tw+=time.perf_counter()-start
    save(out/'gates.json',dict(cases=gates,complete_before_registered_comparators=True))
    timings.update(baseline_application=tp,oracle_solve=to,certificate_serialization=tw)
    t=time.perf_counter()
    for seed,case in inputs.items():
        single=price_table(case,m,(0,),4)
        for K in BUDGETS:
            for name,cal in CALENDARS.items():
                plans={arm:simulate(case,K,cal,table,cap,arm) for arm,table,cap in (
                    ('W06_standby_three',cached[seed],0),('W06_one_three',cached[seed],1),
                    ('robust_three',cached[seed],K),('robust_single',single,K))}
                save(out/'outcomes'/f'{seed}_{K}_{name}.json.gz',plans)
    timings['registered_policy_comparison_and_serialization']=time.perf_counter()-t
    t=time.perf_counter();save(out/'small_optimum.json',small());timings['small_exact_economics']=time.perf_counter()-t
    t=time.perf_counter();check(out);timings['independent_verification']=time.perf_counter()-t
    timings['total_in_process_s']=time.perf_counter()-ti
    timings['peak_process_ru_maxrss_native']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    save(out/'timing.json',timings)

if __name__=='__main__':
    dest=Path(sys.argv[2]).resolve()
    if sys.argv[1]=='freeze':freeze(dest)
    elif sys.argv[1]=='run':run(dest)
    else:raise SystemExit('Use freeze or run with an output directory')
