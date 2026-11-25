"""W04-A, transient restricted heuristics feeding complete unrestricted MIP starts."""
import argparse
import gzip
import hashlib
import json
import os
import platform
import resource
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
FOUND = Path(os.getenv("W03_FOUNDATION", HERE.parent / "foundation")).resolve()
sys.path.insert(0, str(FOUND / "src"))
# W03 common creates an output directory at import. Keep it away from original sources.
os.environ.setdefault("W03_RESULTS", str(Path(tempfile.gettempdir()) / "w04a_model_cache"))
from battery_inputs import make_case
from battery_model import arrays, model, validate, lp_lower, refine
from common import save, finite_bound
import highspy as hs
import numpy as np

ARMS = ["full_milp", "full_lp", "lp_repair_start", "group_start", "group_no_transfer"]
SEEDS = [10403, 10429, 10433, 10501, 10513, 10531]
COHORTS = ["ordinary", "negative_outage", "forced_opposition", "interchangeable"]
SIZES = [(4, 8), (8, 12), (12, 16)]
CLOCKS = [.05, .1, .25, .5, 1., 2.]
BUDGET = 2.
PRACTICAL = .001
def hash_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def complete_start(a, c, d, groups):
    energy = a['initial'][:, None] + np.cumsum(a['eta_c'][:, None]*c - d/a['eta_d'][:, None], axis=1)
    grid = a['load'] + (c-d).sum(axis=0)
    modes = np.array([c[g].max(axis=0)>d[g].max(axis=0) for g in groups], float)
    return np.r_[c.ravel(), d.ravel(), energy.ravel(), grid, modes.ravel()]


def trial(a, arm, rep, frac, presolve, temp):
    start = time.perf_counter()
    now = lambda: time.perf_counter()-start
    n,t = a['n'],a['t']
    units = [[i] for i in range(n)]
    r = dict(case=a['id'],cohort=a['cohort'],n=n,t=t,arm=arm,repeat=rep,
             events=[],stages=[],witnesses=[],target=None,resource_start=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    best,lower=float('inf'),-float('inf')
    powers=None
    source=None
    def assess(stamp):
        if stamp<=BUDGET and r['target'] is None and np.isfinite(best) and np.isfinite(lower):
            if lower>best+2e-5: raise ValueError(('contradictory bounds',a['id'],best,lower))
            if best-lower<=2e-5+.001*max(1,abs(best)):r['target']=stamp
    def lower_event(value,tag):
        nonlocal lower
        stamp=now()
        if value is not None and value>lower and stamp<=BUDGET:
            lower=value;r['events'].append(dict(at=stamp,L=lower,stage=tag));assess(stamp)
    def candidate(c,d,tag,stage,final=False):
        nonlocal best,powers,source
        before=now()
        check=validate(a,c,d)
        stamp=now()
        if stage is not None:stage['validation_seconds']+=stamp-before
        improve=check['valid'] and check['cost']<best-1e-7 and stamp<=BUDGET
        if improve or final:
            ident=len(r['witnesses'])
            r['witnesses'].append(dict(id=ident,stage=tag,at=stamp,**check,c=c.tolist(),d=d.tolist()))
            if improve:
                best=check['cost'];powers=(c.copy(),d.copy());source=tag
                r['events'].append(dict(at=stamp,U=best,stage=tag,witness=ident))
                assess(stamp)
            if stage is not None and final:stage['return_witness']=ident
    fallback=(a['fallback_charge'],a['fallback_discharge'])
    candidate(*fallback,'fallback',None)
    if powers is None:raise ValueError(('invalid fallback',a['id']))
    f0=best
    def solve(label,groups,end,kind='mixed',modes=None,partial=None,full=False,warm=None,warm_label=None):
        stamp=now()
        if stamp>=end:return None,None
        m,ic,idd=model(a,groups,kind,modes)
        if partial is not None:
            z0=len(m.lo)-n*t
            for j,v in enumerate(partial.ravel()):
                if v>=0:m.lo[z0+j]=m.hi[z0+j]=int(v)
        mip=any(m.integer)
        h=m.solver(presolve if mip else 'on',1e-6)
        logfile=Path(temp)/(label+'.log')
        h.setOptionValue('log_file',str(logfile))
        h.setOptionValue('output_flag',True);h.setOptionValue('log_to_console',False)
        stage=dict(label=label,groups=len(groups),original_binary_count=int(sum(m.integer)),rows=len(m.lhs),
                   columns=len(m.lo),full_model=full,build_seconds=now()-stamp,validation_seconds=0.)
        r['stages'].append(stage)
        if warm is not None:
            passed=now();vec=complete_start(a,*warm,groups)
            ax=m.A@vec
            err=max(0,max(np.array(m.lo)-vec),max(vec-np.array(m.hi)),max(np.array(m.lhs)-ax),max(ax-np.array(m.rhs)))
            stage['start_matrix_residual']=float(err)
            stage['start_source']=warm_label
            if err<=2e-6:
                idx=np.arange(len(vec),dtype=np.int32)
                stage['start_set_status']=str(h.setSolution(len(vec),idx,vec))
            else:stage['start_set_status']='incompatible_with_stage'
            stage['start_check_transfer_seconds']=now()-passed
        def interrupt(ev):
            if full:lower_event(finite_bound(ev.data_out.mip_dual_bound),'unrestricted_dual')
            if now()>=end:ev.interrupt()
        def improving(ev):
            x=np.asarray(ev.data_out.mip_solution)
            if len(x)==len(m.lo):candidate(x[ic],x[idd],label,stage)
            if full:lower_event(finite_bound(ev.data_out.mip_dual_bound),'unrestricted_dual')
        if mip:
            h.cbMipInterrupt.subscribe(interrupt);h.cbMipImprovingSolution.subscribe(improving)
        available=end-now()
        if available<=0:
            stage['status']='build_exhausted_budget';return None,None
        h.setOptionValue('time_limit',available)
        solve_start=now();h.run();stage['solve_with_callbacks_seconds']=now()-solve_start
        stage['status']=h.modelStatusToString(h.getModelStatus())
        info=h.getInfo();sol=h.getSolution();c=d=None
        if sol.value_valid and info.primal_solution_status==hs.kSolutionStatusFeasible:
            x=np.asarray(sol.col_value);c,d=x[ic],x[idd];candidate(c,d,label,stage,True)
        if full:lower_event(finite_bound(info.mip_dual_bound),'unrestricted_dual')
        if label=='full_lp' and sol.dual_valid:
            lower_event(lp_lower(m,sol.row_dual),'lp_box_dual')
            if arm=='full_lp' and rep==0:r['lp_dual']=list(sol.row_dual)
        h.setOptionValue('log_file','')
        if logfile.exists():
            lines=logfile.read_text().splitlines()
            stage['solver_evidence']=[s.strip() for s in lines if any(x in s.lower() for x in ('mip start','presolv','assessing feasibility','infeasibilities','timing'))]
            stage['start_confirmed_feasible']=any('mip start solution is feasible' in s.lower() for s in lines)
        stage['end']=now()
        return c,d
    if arm=='full_milp':
        solve('unrestricted',units,BUDGET,full=True,warm=fallback,warm_label='fallback')
    else:
        c,d=solve('full_lp',units,BUDGET,kind='lp')
        if arm!='full_lp' and r['target'] is None:
            candidate_end=BUDGET*frac
            if arm=='lp_repair_start' and c is not None:
                signs=(c>=d).astype(float)
                solve('sign_fix',units,candidate_end,modes=signs)
                # Retain confidence-only LP directions. Ambiguous and idle device-hours are free.
                sure=np.where((c>2e-6)&(d<=2e-6),1,np.where((d>2e-6)&(c<=2e-6),0,-1))
                if r['target'] is None:solve('partial_sign_repair',units,candidate_end,partial=sure,warm=powers,warm_label=source)
            elif arm.startswith('group_'):
                groups=[list(range(n))]
                while len(groups)<n and now()<candidate_end and r['target'] is None:
                    # Split after at most half the candidate budget in any one restriction.
                    solve('shared_'+str(len(groups)),groups,min(candidate_end,now()+candidate_end*.50),
                          warm=powers,warm_label=source)
                    groups=refine(groups,c,d)
            if r['target'] is None:
                use_group=arm!='group_no_transfer'
                solve('unrestricted',units,BUDGET,full=True,warm=powers if use_group else fallback,
                      warm_label=source if use_group else 'fallback')
    r['wall']=now();r['resource_end']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    r['snapshots']={}
    for clock in CLOCKS:
        track=[ev for ev in r['events'] if ev['at']<=clock]
        us=[e for e in track if 'U' in e];ls=[e for e in track if 'L' in e]
        r['snapshots'][str(clock)]=dict(U=us[-1]['U'] if us else None,L=ls[-1]['L'] if ls else None,
                                        source=us[-1]['stage'] if us else None)
    r['fallback_cost']=f0
    return r


def inputs():
    cases=[]
    for n,t in SIZES:
        for j,seed in enumerate(SEEDS):
            for cohort in COHORTS:
                a=make_case(seed,n,t,cohort)
                if cohort in ('ordinary','negative_outage') and j%2:
                    a['terminal_tolerance']=.035*a['capacity']
                cases.append(a)
    return cases


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['prepare','run'])
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    out=args.out.resolve();out.mkdir(parents=True,exist_ok=True)
    if args.action=='prepare':
        if (out/'freeze.json').exists():raise ValueError('Already frozen')
        dev=[arrays(r) for r in json.loads((FOUND/'inputs/battery_holdout.json').read_text()) if r['cohort']=='forced_opposition']
        # Shared tuning contest; all settings run on the same two previous 4x8 and first 8x12 case.
        tuning=[]
        with tempfile.TemporaryDirectory() as tmp:
            for j,a in enumerate(dev[:3]):
                for f in ([.1,.2,.3] if j%2==0 else [.3,.2,.1]):
                    for arm in ['lp_repair_start','group_start']:
                        with tempfile.TemporaryDirectory(dir=tmp) as log:
                            row=trial(a,arm,0,f,'on',log);tuning.append(dict(share=f,trial=row))
        score={}
        for f in [.1,.2,.3]:
            rs=[x['trial'] for x in tuning if x['share']==f]
            norm=lambda r:(r['fallback_cost']-r['snapshots']['2.0']['U'])/max(1,abs(r['fallback_cost']))
            score[f]=(sum(r['target'] is not None for r in rs),float(np.mean([norm(r) for r in rs])),
                      -float(np.mean([r['target'] or BUDGET for r in rs])))
        selected=max(score,key=score.get)
        with gzip.open(out/'development.json.gz','wt') as f:json.dump(tuning,f,allow_nan=False)
        save(out/'instances.json',inputs())
        save(out/'freeze.json',dict(created_utc=datetime.now(timezone.utc).isoformat(),selected_share=selected,
            tuning_scores=score,practical_improvement='0.001 * max(1, abs(case fallback cost)); negative difference favors grouping',
            fraction_measured_from_trial_start=True,fresh_seeds=SEEDS,sizes=SIZES,cohorts=COHORTS,policies=ARMS,
            repeats=3,snapshots_seconds=CLOCKS,budget_seconds=BUDGET,case_success='all three repeats',presolve='on',
            gap='U-L <= 0.00002 + 0.001 max(1,abs(U))',validation_tolerance=2e-6,
            clock='monotonic wall; validate before credit; rank capped time at 2.0; rotate arms.',
            planned_analysis='Case-level median paired U differences at .25s and 2s vs direct MILP and LP repair. Median capped target time; 5000 case bootstrap intervals per cohort. Secondary: normalized primal integral using offline case full-LP lower and incumbent trajectory, fallback until first event. Predeclared mechanism fails absent increased target attainment or median practical cost improvement relative to LP repair and direct MILP; attribution checked against identical grouping without transfer.',
            seeds_tolerance='odd index in fresh seed list: 3.5% endpoint tolerance in ordinary/negative_outage only; forced/interchangeable cyclic',
            start='full primal vector reconstructed and model-row/box-checked. Feasibility confirmation requires HiGHS log. Stage timings include file logging.',
            tuning='W03 full-MILP presolve winner on; share .1/.2/.3 across both start policies on three W03 hard cases; maximize target hits then mean normalized quality then minimized capped mean latency.',
            system=platform.platform(),cpus=os.cpu_count(),python=sys.version,highs=hs.Highs().version(),threads=1,
            sha256={p.name:hash_file(p) for p in [Path(__file__),HERE/'analysis.py',HERE/'protocol/plan.md',FOUND/'src/common.py',
            FOUND/'src/battery_model.py',FOUND/'src/battery_inputs.py',FOUND/'src/battery_audit.py',FOUND/'requirements.txt',
            out/'development.json.gz',out/'instances.json']}))
        print('frozen share',selected,flush=True)
        return
    frozen=json.loads((HERE/'protocol/freeze.json').read_text())
    for p in [Path(__file__),HERE/'analysis.py',HERE/'protocol/plan.md',HERE/'protocol/instances.json',
              FOUND/'src/common.py',FOUND/'src/battery_model.py',FOUND/'src/battery_inputs.py',FOUND/'src/battery_audit.py',
              FOUND/'requirements.txt']:
        if hash_file(p)!=frozen['sha256'][p.name]:raise ValueError('Frozen input changed: '+p.name)
    dest=out/'trials.jsonl.gz'
    if dest.exists():raise ValueError('Choose a fresh output directory')
    cases=json.loads((HERE/'protocol/instances.json').read_text())
    with gzip.open(dest,'wt') as stream:
        for j,rec in enumerate(cases):
            a=arrays(rec)
            for rep in range(3):
                offset=(j+2*rep)%len(ARMS)
                for arm in ARMS[offset:]+ARMS[:offset]:
                    with tempfile.TemporaryDirectory() as temp:
                        row=trial(a,arm,rep,frozen['selected_share'],'on',temp)
                    stream.write(json.dumps(row,allow_nan=False,separators=(',',':'))+'\n')
            print(a['id'],flush=True)
if __name__=='__main__':main()
