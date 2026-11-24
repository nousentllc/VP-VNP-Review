"""Issued-forecast replay for a synthetic computing load and single behind-the-meter BESS."""
import argparse
import importlib.util
import json
import tempfile
import time
from pathlib import Path
import numpy as np
from scipy.optimize import linprog
from common import ROOT,OUT,DESIGN,save

CFG=DESIGN['E']
PARAM=dict(energy=180., initial=95., eta_c=.94,eta_d=.93,power=35.,grid_cap=100.,previous=85.,
           ramp=23.,facility=24.,online_deadline=1.,physical_tolerance=1e-6)


def generate():
    cases=[]
    for seed in CFG['seeds']:
        for regime in CFG['regimes']:
            # Regimes use the same latent day for a seed. Forecast perturbations are drawn separately.
            rng=np.random.default_rng(seed);frng=np.random.default_rng(seed+700)
            start=int(rng.integers(8,14));length=int(rng.integers(3,7))
            plan=np.full(24,84.)+rng.uniform(-3,3,24)
            plan[start:start+length]+=rng.uniform(29,49)
            shockhour=int(rng.integers(5,18));unexpected=rng.uniform(9,26)
            residual=np.zeros(24)
            for h in range(24):
                residual[h]=(.52*residual[h-1] if h else 0.)+rng.normal(0,4)+(unexpected if h==shockhour else 0)
            actual=np.maximum(80.,plan+residual)
            basefloor=55. if regime=='outage_reserve' else 35.
            floor=basefloor+(95-basefloor)*np.clip((np.arange(24)-17)/6,0,1)
            offline=np.zeros(24,dtype=bool)
            reserve=np.zeros(24)
            if regime=='outage_reserve':
                offline[start+1:start+3]=True
                reserve[start-2:start+length+1]=8.
            issues=[]
            for h in range(24):
                idx=np.arange(h,min(24,h+CFG['lookahead']))
                lead=idx-h
                fc=plan[idx]+(.52**lead)*residual[h]+frng.normal(0,2.5,len(idx))
                if regime=='biased_forecast':fc-=np.minimum(lead,2)*4.5
                fc=np.maximum(80.,fc);fc[0]=actual[h]
                # The current battery state is observed. Outage disclosure extends one hour ahead.
                avail=np.where(lead<=1,~offline[idx],True)
                issues.append(dict(issue=h,valid=idx,load=fc,available=avail))
            cases.append(dict(id=f'{regime}_{seed}',regime=regime,seed=seed,load=actual,floor=floor,
                              available=~offline,reserve=reserve,issues=issues))
    save(ROOT/'inputs/load_forecasts.json',dict(parameters=PARAM,cases=cases))


def rule(load,avail,floors,reserve,e,prev):
    p=PARAM
    cap=p['grid_cap'];hi=min(cap,prev+p['ramp'])
    charge_limit=p['power']*avail[0]
    discharge_limit=max(0.,charge_limit-reserve[0])*avail[0]
    target=max(p['initial'],max(floors),max(floors)+sum(max(0,x-cap) for x in load[1:])/p['eta_d'])
    target=min(target,p['energy'])
    required=max(0.,(floors[0]-e)/p['eta_c'])
    dis=min(discharge_limit,max(0.,load[0]-hi),max(0.,e-floors[0])*p['eta_d'])
    ch=0.
    if dis<=1e-10:
        ch=min(charge_limit,(p['energy']-e)/p['eta_c'],
               max(required,min(max(0.,hi-load[0]),max(0.,target-e)/p['eta_c'])))
    g=min(hi,load[0]+ch-dis)
    u=load[0]-g+ch-dis
    return np.array([g,ch,dis,max(0,u),e+p['eta_c']*ch-dis/p['eta_d']])


def lp(load,avail,floors,reserve,e,prev):
    p=PARAM;t=len(load);N=5*t
    ids=np.arange(N).reshape(t,5)
    eq=[];rhs=[];ub=[];upper=[];bounds=[]
    for h,(g,ch,ds,u,soc) in enumerate(ids):
        row=np.zeros(N);row[[g,ch,ds,u]]=[1,-1,1,1];eq.append(row);rhs.append(load[h])
        row=np.zeros(N);row[[soc,ch,ds]]=[1,-p['eta_c'],1/p['eta_d']]
        if h:row[ids[h-1,4]]=-1
        eq.append(row);rhs.append(0. if h else e)
        row=np.zeros(N);row[g]=1
        if h:row[ids[h-1,0]]=-1
        ub.extend([row,-row]);upper.extend([p['ramp']+(prev if h==0 else 0.),p['ramp']-(prev if h==0 else 0.)])
        power=p['power']*avail[h]
        bounds.extend([(0,p['grid_cap']),(0,power),(0,max(0.,power-reserve[h])),
                       (0,load[h]-p['facility']),(floors[h],p['energy'])])
    cost=np.zeros(N);cost[ids[:,3]]=1
    sol=linprog(cost,A_ub=ub,b_ub=upper,A_eq=eq,b_eq=rhs,bounds=bounds,method='highs')
    if not sol.success:return None,sol.message
    # Lexicographic solution. The first-stage unserved total is retained at numerical precision.
    eq.append(cost.copy());rhs.append(sol.fun)
    cost[:]=0.;cost[ids[:,1:3]]=1.
    sol=linprog(cost,A_ub=ub,b_ub=upper,A_eq=eq,b_eq=rhs,bounds=bounds,method='highs')
    if not sol.success:return None,sol.message
    return sol.x.reshape(t,5),'optimal'


def check(action,e,prev,load,avail,floor,reserve):
    p=PARAM;g,ch,ds,u,end=action
    limit=p['power']*avail
    return float(max(0.,abs(g+ds-ch+u-load),abs(end-e-p['eta_c']*ch+ds/p['eta_d']),
                    floor-end,end-p['energy'],-g,g-p['grid_cap'],abs(g-prev)-p['ramp'],
                    -u,u-load+p['facility'],-ch,-ds,ch-limit,ds-max(0.,limit-reserve),min(ch,ds)))


def trial(case,method):
    p=PARAM;available=np.array(case['available']);floor=np.array(case['floor']);reserve=np.array(case['reserve'])
    actual=np.array(case['load']);e=p['initial'];prev=p['previous']
    first=time.perf_counter();rv=[];fallback=[];late=[];maxerr=0.;issue_times=[]
    if method=='perfect_foresight':
        plan,status=lp(actual,available,floor,reserve,e,prev)
        if plan is None:raise ValueError(status)
    for h,issue in enumerate(case['issues']):
        stamp=time.perf_counter();idx=np.array(issue['valid']);forecast=np.array(issue['load'])
        avail=np.array(issue['available']);floors=floor[idx];rs=reserve[idx]
        if forecast[0]!=actual[h] or avail[0]!=available[h]:raise ValueError('Issue timestamp mismatch')
        if method=='perfect_foresight':action=plan[h]
        elif method=='forecast_rule':action=rule(forecast,avail,floors,rs,e,prev)
        else:
            opt,status=lp(forecast,avail,floors,rs,e,prev)
            action=None if opt is None else opt[0]
        err=1e20 if action is None else check(action,e,prev,actual[h],available[h],floor[h],reserve[h])
        latency=time.perf_counter()-stamp
        if method!='perfect_foresight' and latency>p['online_deadline']:late.append(h)
        if err>p['physical_tolerance'] or h in late:
            if method=='perfect_foresight':raise ValueError((case['id'],h,err))
            fallback.append(h)
            action=rule(forecast[:1],avail[:1],floors[:1],rs[:1],e,prev)
            err=check(action,e,prev,actual[h],available[h],floor[h],reserve[h])
            if err>p['physical_tolerance']:raise ValueError((case['id'],'fallback',h,err))
        maxerr=max(maxerr,err);prev=action[0];e=action[4];rv.append(action.tolist())
        issue_times.append(time.perf_counter()-stamp)
    arr=np.array(rv);g,ch,ds,u,s=arr.T
    return dict(case=case['id'],regime=case['regime'],method=method,actions=rv,
                unserved_MWh=sum(u),useful_compute_MWh=sum(actual-p['facility']-u),
                conversion_loss_MWh=sum((1-p['eta_c'])*ch+(1/p['eta_d']-1)*ds),
                throughput_MWh=sum(ch+ds),peak_import_MW=max(g),grid_MWh=sum(g),
                terminal_MWh=e,min_reserve_margin_MWh=min(s-floor),
                unavailable_contracted_headroom_MWh_equivalent=sum(reserve*~available),
                invalid_or_late_fallback_hours=fallback,late=late,max_violation=maxerr,
                seconds=time.perf_counter()-first,issue_seconds=issue_times)


def run():
    spec=importlib.util.spec_from_file_location('legacy',ROOT/'inputs/legacy/run_benchmarks.py')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    out=OUT/'E';out.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        legacy=mod.bess_benchmark(Path(tmp))
    save(out/'legacy_replay.json',legacy)
    cases=json.loads((ROOT/'inputs/load_forecasts.json').read_text())['cases']
    result=[trial(case,m) for case in cases for m in CFG['methods']]
    save(out/'runs.json',result)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['generate','run'])
    if ap.parse_args().action=='generate':generate()
    else:run()
