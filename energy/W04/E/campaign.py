"""W04-E simulation. All energies are MWh, powers MW; intervals last one hour."""
import argparse
import gzip
import hashlib
import json
import os
import sys
import time
import warnings
from pathlib import Path

for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):
    os.environ[name] = '1'
ROOT = Path(__file__).resolve().parent
FOUNDATION = ROOT.parent/'foundation'
sys.path.insert(0, str(FOUNDATION/'src'))
import numpy as np
import scipy
from scipy.optimize import linprog, OptimizeWarning
import load_control as old

P = old.PARAM
# SciPy passes threads and parallel through to HiGHS. Pin the thread count and dual simplex.
OPTIONS = {'threads':1, 'parallel':False, 'presolve':True,'primal_feasibility_tolerance':1e-8,
           'dual_feasibility_tolerance':1e-8, 'simplex_dual_edge_weight_strategy':'devex'}
warnings.filterwarnings('ignore', category=OptimizeWarning, message='Unrecognized options.*')
def single_thread_legacy(*args, **kwargs):
    kwargs['options']={**kwargs.get('options',{}),'threads':1,'parallel':False}
    return linprog(*args,**kwargs)

old.linprog=single_thread_legacy
HORIZONS=(3,6,12)
POLICIES=[f'{m}{h}' for h in HORIZONS for m in ('rule','none','value')]+['legacy6','value12_tail6','offline']


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path, obj):
    def custom(x):
        if isinstance(x,np.ndarray):return x.tolist()
        if isinstance(x,np.generic):return x.item()
        raise TypeError(type(x).__name__)
    data=json.dumps(obj,default=custom,allow_nan=False,separators=(',',':'),sort_keys=True).encode()
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.suffix=='.gz': data=gzip.compress(data,compresslevel=6,mtime=0)
    path.write_bytes(data)


def read(path):
    raw=path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix=='.gz' else raw)


def panel(seeds):
    """Call W03's generator once per panel with maximum issue horizon; capture output in memory."""
    previous=dict(old.CFG); writer=old.save
    data=[]
    try:
        old.CFG.update(seeds=list(seeds),lookahead=12)
        old.save=lambda _path,obj:data.append(obj)
        old.generate()
    finally:
        old.CFG.clear();old.CFG.update(previous);old.save=writer
    return data[0]


def calibrate(cases):
    """Training-only conditional extra SOC after a window, from out-of-window net deficits."""
    buckets=[[] for _ in range(6)]
    for c in cases:
        if c['regime']!='base':continue
        for boundary in range(23):
            suffix=np.asarray(c['load'][boundary+1:boundary+7])
            deficit=np.clip(suffix-P['grid_cap'],-P['power'],P['power'])
            drain=np.where(deficit>0,deficit/P['eta_d'],deficit*P['eta_c'])
            need=max(0.,float(max(np.cumsum(drain))))
            buckets[boundary//4].append(need)
    return dict(q=.75, lookahead_after_boundary=6,
                extra=[float(np.quantile(b,.75,method='linear')) for b in buckets],
                sample_counts=[len(b) for b in buckets], training_needs=buckets)


def matrix(load,available,floors,reserve,e,prev):
    H=len(load); idx=np.arange(H*5).reshape(H,5)
    eq=[]; rhs=[]; ub=[]; limits=[]; boxes=[]
    for j,(g,c,d,u,s) in enumerate(idx):
        row=np.zeros(5*H);row[[g,c,d,u]]=[1,-1,1,1];eq.append(row);rhs.append(load[j])
        row=np.zeros(5*H);row[[s,c,d]]=[1,-P['eta_c'],1/P['eta_d']]
        if j:row[idx[j-1,4]]=-1
        eq.append(row);rhs.append(0. if j else e)
        row=np.zeros(5*H);row[g]=1
        if j:row[idx[j-1,0]]=-1
        ub.extend([row,-row]);limits.extend([P['ramp']+(0 if j else prev),P['ramp']-(0 if j else prev)])
        pl=P['power']*available[j]
        boxes.extend([(0,P['grid_cap']),(0,pl),(0,max(0,pl-reserve[j])),(0,load[j]-P['facility']),(floors[j],P['energy'])])
    return idx,eq,rhs,ub,limits,boxes


def lex_plan(load,avail,floors,reserve,e,prev,target=None,tie='early_service',forced_first=None):
    """Only the applied action must be unique. Service, then continuation, then throughput;
    then three scalar action objectives uniquely identify the five applied components."""
    idx,eq,rhs,ub,limits,boxes=matrix(load,avail,floors,reserve,e,prev)
    N=idx.size;stages={}
    if forced_first is not None:
        for i,val in enumerate(forced_first):boxes[i]=(float(val),float(val))
    def solve(indices,weight,stage,retain=True):
        objective=np.zeros(N);objective[np.ravel(indices)]=weight
        sol=linprog(objective,A_ub=ub,b_ub=limits,A_eq=eq,b_eq=rhs,bounds=boxes,
                    method='highs-ds',options=OPTIONS)
        if not sol.success:raise RuntimeError(stage+': '+sol.message)
        stages[stage]=float(sol.fun)
        if retain:eq.append(objective);rhs.append(float(sol.fun))
        return sol.x.reshape(-1,5)
    solve(idx[:,3],1,'forecast_unserved')
    if target is not None and target>floors[-1]+1e-8:
        sol=solve([idx[-1,4]],-1,'negative_maximum_end_soc',False)
        achieved=min(float(target),sol[-1,4])
        boxes[idx[-1,4]]=(max(floors[-1],achieved),P['energy'])
        stages['minimum_shortfall']=max(0.,target-achieved)
    trajectory=solve(idx[:,1:3],1,'throughput',tie is not None)
    if tie is not None:
        trajectory=solve([idx[0,3]],1 if tie=='early_service' else -1,'current_shed_tiebreak')
        trajectory=solve([idx[0,1]],1,'current_charge_tiebreak')
        trajectory=solve([idx[0,2]],1,'current_discharge_tiebreak',False)
    return trajectory,stages


def simulate(c,policy,fit,tie='early_service'):
    e=P['initial'];prev=P['previous'];actions=[];hourlog=[]
    load=np.asarray(c['load']);availability=np.asarray(c['available']);floors=np.asarray(c['floor']);reserve=np.asarray(c['reserve'])
    if policy=='offline':
        stamp=time.perf_counter()
        full,offdiag=old.lp(load,availability,floors,reserve,e,prev)
        offsec=time.perf_counter()-stamp
        if full is None:raise ValueError(offdiag)
    for h,issue in enumerate(c['issues']):
        stamp=time.perf_counter()
        H=12 if policy in ('offline','value12_tail6') else int(''.join(z for z in policy if z.isdigit()))
        idx=np.asarray(issue['valid'][:H]);fc=np.asarray(issue['load'][:H]);avail=np.asarray(issue['available'][:H])
        if policy=='value12_tail6' and len(fc)>6:fc[6:]=fc[5]
        if fc[0]!=load[h] or avail[0]!=availability[h]:raise ValueError('invalid issue')
        fs=floors[idx];rs=reserve[idx];stage={};target=None;failure=None
        # Precompute and validate the same one-step fallback before issuing each online decision.
        fallback=old.rule(fc[:1],avail[:1],fs[:1],rs[:1],e,prev)
        if old.check(fallback,e,prev,load[h],availability[h],fs[0],rs[0])>1e-6:raise ValueError('invalid fallback')
        try:
            if policy=='offline':act=full[h]
            elif policy.startswith('rule'):act=old.rule(fc,avail,fs,rs,e,prev)
            elif policy=='legacy6':
                path,msg=old.lp(fc,avail,fs,rs,e,prev)
                if path is None: raise RuntimeError(msg)
                act=path[0]
            else:
                if policy.startswith('value'):
                    target=min(P['energy'],float(fs[-1])+fit['extra'][idx[-1]//4]) if idx[-1]<23 else fs[-1]
                path,stage=lex_plan(fc,avail,fs,rs,e,prev,target,tie);act=path[0]
            err=old.check(act,e,prev,load[h],availability[h],fs[0],rs[0])
            if err>1e-6:raise RuntimeError('physical violation '+str(err))
        except RuntimeError as exc:
            failure=str(exc);act=fallback
        ready=time.perf_counter()-stamp
        if policy!='offline' and ready>P['online_deadline']:
            failure=(failure+'; ' if failure else '')+'deadline';act=fallback
        actions.append(np.asarray(act).tolist())
        hourlog.append(dict(issue=h,horizon=len(idx),end_target=target,objectives=stage,fallback=failure,
                            ready_seconds=ready))
        prev=act[0];e=act[4]
    g,ch,ds,u,s=np.array(actions).T
    return dict(case=c['id'],regime=c['regime'],seed=c['seed'],policy=policy,actions=actions,
                decisions=hourlog,unserved=float(sum(u)),served=float(sum(load-P['facility']-u)),
                losses=float(sum((1-P['eta_c'])*ch+(1/P['eta_d']-1)*ds)),throughput=float(sum(ch+ds)),
                grid=float(sum(g)),peak=float(max(g)),terminal=e,min_floor_margin=float(min(s-floors)),
                unavailable_headroom=float(sum(reserve*~availability)),offline_solve_seconds=offsec if policy=='offline' else None)


def development():
    historical=read(FOUNDATION/'inputs/load_forecasts.json')['cases']
    stored=read(FOUNDATION/'results/E/runs.json')
    fresh=[old.trial(c,m) for c in historical for m in old.CFG['methods']]
    keyed={(r['case'],r['method']):r for r in stored}
    diff=max(np.max(np.abs(np.asarray(r['actions'])-keyed[r['case'],r['method']]['actions'])) for r in fresh)
    review=read(ROOT/'inputs/reviewer_864.json')
    a=keyed['outage_reserve_864','rolling_mpc'];b=review['trajectory']
    diffs=np.max(np.abs(np.asarray(a['actions'])-np.asarray(b['actions'])),axis=1)
    t=int(np.flatnonzero(diffs>1e-6)[0]);case=next(c for c in historical if c['id']==a['case'])
    issue=case['issues'][t];idx=issue['valid'];e=a['actions'][t-1][4];prev=a['actions'][t-1][0]
    args=(issue['load'],issue['available'],np.array(case['floor'])[idx],np.array(case['reserve'])[idx],e,prev)
    alternatives={}
    for name,act in [('mac',a['actions'][t]),('linux',b['actions'][t]),('unfixed',None)]:
        sol,stages=lex_plan(*args,tie=None,forced_first=act)
        alternatives[name]=dict(plan=sol,stages=stages)
    fit=calibrate(historical)
    newdev=panel(old.CFG['seeds'])['cases']
    rows=[simulate(c,'none6',fit,tie) for c in newdev for tie in ('early_service','deferred_service')]
    tie_comp=[dict(case=c['id'],early=rows[2*i]['unserved'],deferred=rows[2*i+1]['unserved']) for i,c in enumerate(newdev)]
    dev=dict(max_W03_action_difference=diff,archived_trajectories=len(fresh),first_divergent_hour=t,
             hours_with_action_difference=np.flatnonzero(diffs>1e-6),mac_unserved=a['unserved_MWh'],linux_unserved=b['unserved_MWh'],
             matched_first_action_subproblems=alternatives,dev_tie_comparison=tie_comp,calibration=fit)
    dump(ROOT/'protocol/development.json',dev);dump(ROOT/'results/W03_replay.json.gz',fresh)
    dump(ROOT/'inputs/holdout.json.gz',panel(range(11001,11025)))


def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['develop','run']);p.add_argument('--out',type=Path)
    args=p.parse_args()
    if args.action=='develop':development();return
    freeze=read(ROOT/'protocol/freeze.json')
    for f,sha in freeze['sha256'].items():
        if digest(ROOT/f)!=sha:raise ValueError('freeze mismatch '+f)
    cases=read(ROOT/'inputs/holdout.json.gz')['cases'];fit=read(ROOT/'protocol/development.json')['calibration']
    out=args.out or ROOT/'results/holdout.jsonl.gz'
    if out.exists():raise FileExistsError(out)
    out.parent.mkdir(parents=True,exist_ok=True)
    with gzip.open(out,'wt') as file:
        for i,c in enumerate(cases):
            arms=POLICIES[i%len(POLICIES):]+POLICIES[:i%len(POLICIES)]
            for m in arms:file.write(json.dumps(simulate(c,m,fit),allow_nan=False)+'\n')
            print(c['id'],flush=True)


if __name__=='__main__':main()
