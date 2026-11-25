"""Serial performance comparison with a common constructive fallback and chronological bounds."""
import argparse
import gzip
import json
import time
import numpy as np
import highspy as hs
from common import ROOT, OUT, DESIGN, save, finite_bound
from battery_model import arrays, model, validate, lp_lower, refine

CFG=DESIGN['A']


def trial(a, policy, presolve, rep):
    start=time.perf_counter()
    deadline=CFG['seconds_per_policy']
    now=lambda: time.perf_counter()-start
    record=dict(case=a['id'],cohort=a['cohort'],policy=policy,repeat=rep,events=[],steps=[],
                first_feasible=None,first_solver_schedule=None,target_time=None,lower=None,upper=None,
                winner=None,lower_kind=None)
    best_schedule=None
    best_by_deadline=None
    def mark(source):
        u,l=record['upper'],record['lower']
        if u is not None and l is not None:
            tol=CFG['target_absolute']+CFG['target_relative']*max(1,abs(u))
            if l>u+2e-5:
                raise ValueError(f'Inconsistent bounds in {a["id"]}: {l}, {u}')
            if u-l<=tol and record['target_time'] is None and now()<=deadline:
                record['target_time']=now()
                record['target_stage']=source
    def bound(val,kind):
        if val is None or now()>deadline: return
        if record['lower'] is None or val>record['lower']:
            record['lower'],record['lower_kind']=val,kind
            record['events'].append(dict(time=now(),source=kind,lower=val))
        mark(kind)
    def candidate(ch,dis,label,step=None):
        nonlocal best_schedule,best_by_deadline
        stamp=now()
        check=validate(a,ch,dis)
        checked=now()
        if step is not None:
            step['validation_seconds']+=checked-stamp
            if not check['valid']: step['invalid_candidates']+=1
        if check['valid'] and checked<=deadline:
            if record['first_feasible'] is None: record['first_feasible']=checked
            if label!='fallback' and record['first_solver_schedule'] is None:
                record['first_solver_schedule']=checked
            if record['upper'] is None or check['cost']<record['upper']-1e-7:
                record['upper'],record['winner']=check['cost'],label
                best_schedule=(ch.copy(),dis.copy())
                best_by_deadline=checked
                record['events'].append(dict(time=checked,source=label,upper=check['cost']))
            mark(label)
        return check
    candidate(a['fallback_charge'],a['fallback_discharge'],'fallback')
    if record['first_feasible'] is None: raise ValueError('Invalid common fallback')
    n,t=a['n'],a['t']
    singles=[[i] for i in range(n)]
    def run(label,groups,kind='mixed',modes=None,symmetry=False,allowed=None,outer=False):
        if now()>=deadline: return None,None
        before=now()
        m,c,d=model(a,groups,kind,modes,symmetry)
        is_lp=kind=='lp' or modes is not None
        h=m.solver('on' if is_lp else presolve,CFG['solver_mip_rel_gap'])
        h.setOptionValue('output_flag',True)
        h.setOptionValue('log_to_console',False)
        build=now()-before
        step=dict(label=label,groups=len(groups),columns=len(m.cost),rows=len(m.lhs),
                  binary=sum(m.integer),build_seconds=build,validation_seconds=0.,invalid_candidates=0,
                  presolve_messages=[],presolve_observed_seconds=None)
        record['steps'].append(step)
        pres=[]
        def logging(ev):
            msg=ev.message.strip()
            if 'presolv' in msg.lower():
                if len(step['presolve_messages'])<12: step['presolve_messages'].append(msg)
                pres.append(now())
        h.cbLogging.subscribe(logging)
        def improving(ev):
            x=np.asarray(ev.data_out.mip_solution)
            if len(x)==len(m.cost):
                candidate(x[c],x[d],label,step)
            if outer: bound(finite_bound(ev.data_out.mip_dual_bound),'full_mip_dual')
        if not is_lp:
            h.cbMipImprovingSolution.subscribe(improving)
            if outer:
                def observe_bound(ev):
                    bound(finite_bound(ev.data_out.mip_dual_bound),'full_mip_dual')
                h.cbMipInterrupt.subscribe(observe_bound)
            fc,fd=a['fallback_charge'],a['fallback_discharge']
            compatible=all(not np.any((fc[group].max(axis=0)>1e-9)&(fd[group].max(axis=0)>1e-9))
                           for group in groups)
            if kind=='proportional':
                compatible=compatible and all(np.max(np.ptp(v[group]/a['capacity'][group,None], axis=0))<1e-9
                                               for v in (fc,fd) for group in groups)
            if compatible:
                inds=np.r_[c.ravel(),d.ravel()].astype(np.int32)
                h.setSolution(len(inds),inds,np.r_[fc.ravel(),fd.ravel()])
            step['partial_mip_start_from_common_fallback']=bool(compatible)
        remaining=deadline-now()
        if allowed is not None: remaining=min(remaining,allowed)
        if remaining<=0:
            step['status']='build_exhausted_deadline'
            return None,None
        h.setOptionValue('time_limit',remaining)
        h.run()
        step['solve_including_callbacks_seconds']=now()-before-build
        step['status']=h.modelStatusToString(h.getModelStatus())
        if len(pres)>1: step['presolve_observed_seconds']=max(pres)-min(pres)
        sol=h.getSolution()
        ch=dis=None
        if h.getInfo().primal_solution_status==hs.kSolutionStatusFeasible and sol.value_valid:
            x=np.asarray(sol.col_value); ch,dis=x[c],x[d]
            check=candidate(ch,dis,label,step)
            step['returned_check']=check
            if rep==0: step['returned_powers']=[ch.tolist(),dis.tolist()]
            step['solver_objective']=h.getObjectiveValue()
        if outer and not is_lp:
            bound(finite_bound(h.getInfo().mip_dual_bound),'full_mip_dual')
        if label=='full_lp' and sol.dual_valid:
            bound(lp_lower(m,sol.row_dual),'full_lp_box_dual')
        step['nodes']=h.getInfo().mip_node_count
        step['end_seconds']=now()
        return ch,dis
    if policy=='full_milp' or policy=='symmetry':
        run(policy,singles,symmetry=policy=='symmetry',outer=True)
    else:
        ch,di=run('full_lp',singles,kind='lp')
        fixed=[list(range(n//2)),list(range(n//2,n))]
        if policy in ('fixed_shared','fixed_proportional'):
            # Report the restriction's own outcome even when the LP was already feasible.
            run(policy,fixed,'proportional' if policy=='fixed_proportional' else 'mixed')
        elif policy=='lp_recovery' and record['target_time'] is None:
            if ch is not None:
                run('lp_fixed_signs',singles,modes=(ch>=di).astype(float),allowed=deadline*.2)
            if record['target_time'] is None: run('full_recovery',singles,outer=True)
        elif policy=='adaptive' and record['target_time'] is None:
            groups=[list(range(n))]
            while len(groups)<n and record['target_time'] is None and now()<deadline:
                run('shared_'+str(len(groups)),groups,allowed=deadline*.12)
                groups=refine(groups,ch,di)
            if record['target_time'] is None: run('singleton_full',singles,outer=True)
    record['elapsed']=now()
    record['best_time']=best_by_deadline
    if rep==0: record['best_powers']=[v.tolist() for v in best_schedule]
    return record


def run(split):
    cases=[arrays(x) for x in json.loads((ROOT/'inputs'/f'battery_{split}.json').read_text())]
    path=OUT/'A';path.mkdir(exist_ok=True)
    if split=='development':
        trials=[]
        for j,a in enumerate(cases):
            for setting in (['on','off'] if j%2==0 else ['off','on']):
                r=trial(a,'full_milp',setting,0)
                trials.append(dict(presolve=setting,**r))
        score={}
        for setting in ['on','off']:
            ts=[r['target_time'] for r in trials if r['presolve']==setting]
            score[setting]=[sum(v is not None for v in ts),
                            -float(np.median([CFG['seconds_per_policy'] if v is None else v for v in ts]))]
        save(path/'development.json',dict(selected=max(score,key=score.get),scores=score,trials=trials))
        return
    setting=json.loads((path/'development.json').read_text())['selected']
    with gzip.open(path/'holdout.jsonl.gz','wt') as f:
        for j,a in enumerate(cases):
            methods=[p for p in CFG['policies'] if p!='symmetry' or a['cohort']=='interchangeable']
            for rep in range(CFG['repeats']):
                offset=(j+rep*2)%len(methods)
                for p in methods[offset:]+methods[:offset]:
                    f.write(json.dumps(trial(a,p,setting,rep),allow_nan=False)+'\n')
            print(a['id'],flush=True)


if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('split',choices=['development','holdout'])
    run(ap.parse_args().split)
