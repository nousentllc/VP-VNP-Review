"""Independent hour-by-hour trajectory replay and preregistered day-cluster contrasts."""
import argparse
import csv
import gzip
import hashlib
import json
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parent


def load_runs(path):
    with gzip.open(path,'rt') as f:
        return {(r['case'],r['policy']):r for r in map(json.loads,f)}


def inspect(c,p,actions):
    arr=np.array(actions)
    if arr.shape!=(24,5) or not np.isfinite(arr).all():raise ValueError('Malformed trajectory')
    grid,charge,dis,shed,soc=arr.T
    load=np.array(c['load']);avail=np.array(c['available']);reserve=np.array(c['reserve'])
    after=p['initial']+np.cumsum(p['eta_c']*charge-dis/p['eta_d'])
    dd=np.diff(np.r_[p['previous'],grid])
    limits=dict(balance=max(abs(grid+dis-charge+shed-load)),soc_reconstruction=max(abs(after-soc)),
                energy_cap=max(soc-p['energy']),floor=max(np.array(c['floor'])-soc),
                terminal=p['initial']-soc[-1],coincident=max(np.minimum(charge,dis)),
                signed=min(0.,arr.min())*-1,grid_cap=max(grid-p['grid_cap']),ramp=max(abs(dd)-p['ramp']),
                charge_limit=max(charge-p['power']*avail),discharge_limit=max(dis-np.maximum(0.,p['power']*avail-reserve)),
                protected_facility=max(shed-load+p['facility']))
    metrics=dict(unserved=sum(shed),served=sum(load-p['facility']-shed),losses=sum(charge*(1-p['eta_c'])+dis*(1/p['eta_d']-1)),
                 grid=sum(grid),throughput=sum(charge+dis),peak=max(grid),terminal=soc[-1],min_floor_margin=min(soc-c['floor']),
                 unavailable_headroom=sum(reserve*~avail))
    return max(limits.values()),metrics


def write_csv(path, rows):
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,rows[0].keys());w.writeheader();w.writerows(rows)


def run(raw,out,repeat):
    out.mkdir(exist_ok=True,parents=True)
    data=json.loads(gzip.decompress((ROOT/'inputs/holdout.json.gz').read_bytes()))
    params=data['parameters'];cases=data['cases']
    runs=load_runs(raw)
    arms=['rule3','rule6','rule12','none3','none6','none12','value3','value6','value12','value12_tail6','legacy6','offline']
    expected={(c['id'],a) for c in cases for a in arms}
    assert set(runs)==expected and len(expected)==864
    residual=0.;outcomes=[]
    scenario={}
    for c in cases:
        for i,issue in enumerate(c['issues']):
            assert issue['issue']==i and issue['valid']==list(range(i,min(i+12,24)))
            assert c['load'][i]==issue['load'][0]
            for j,idx in enumerate(issue['valid']):
                assert issue['available'][j]==(c['available'][idx] if j<=1 else True)
        for m in arms:
            r=runs[c['id'],m];err,vals=inspect(c,params,r['actions'])
            residual=max(residual,err)
            assert err<=1e-6 and all(abs(vals[k]-r[k])<=1e-6 for k in vals)
            assert vals['unserved']>=runs[c['id'],'offline']['unserved']-1e-6
            times=[d['ready_seconds'] for d in r['decisions']]
            outcomes.append(dict(case=c['id'],day=c['seed'],regime=c['regime'],policy=m,**vals,
                                 fallback=sum(d['fallback'] is not None for d in r['decisions']),
                                 seconds_total=sum(times),seconds_max=max(times),
                                 offline_planning_seconds=r.get('offline_solve_seconds')))
            scenario[c['seed'],c['regime'],m]=r
    write_csv(out/'scenario_metrics.csv',outcomes)
    metrics=['unserved','served','losses','throughput','grid','unavailable_headroom']
    regimes=['base','biased_forecast','outage_reserve'];seeds=sorted({c['seed'] for c in cases})
    group=[]
    for reg in regimes:
        for a in arms:
            rr=[scenario[s,reg,a] for s in seeds];ds=[d for r in rr for d in r['decisions']]
            group.append(dict(regime=reg,policy=a,days=len(rr),**{k:sum(r[k] for r in rr) for k in metrics},
                              peak=max(r['peak'] for r in rr),min_terminal=min(r['terminal'] for r in rr),
                              p95_ready_ms=1000*np.quantile([d['ready_seconds'] for d in ds],.95),
                              max_ready_ms=1000*max(d['ready_seconds'] for d in ds),fallback=sum(d['fallback'] is not None for d in ds)))
    write_csv(out/'regime_totals.csv',group)
    pairs=[('value6','rule6'),('value6','none6'),('none6','rule6'),('none6','legacy6'),
           ('value3','none3'),('value12','none12'),('value3','rule3'),('value12','rule12'),
           ('none3','rule3'),('none12','rule12'),('value12','value6'),('value6','value3'),
           ('none12','none6'),('none6','none3'),('value12','value12_tail6'),('value12_tail6','value6')]
    rng=np.random.default_rng(665411);idx=rng.integers(0,len(seeds),size=(10000,len(seeds)))
    comparisons=[];byday=[]
    for a,b in pairs:
        for reg in ['all',*regimes]:
            selected=regimes if reg=='all' else [reg]
            d=np.array([np.mean([scenario[s,g,a]['unserved']-scenario[s,g,b]['unserved'] for g in selected]) for s in seeds])
            losses=np.array([np.mean([scenario[s,g,a]['losses']-scenario[s,g,b]['losses'] for g in selected]) for s in seeds])
            cycling=np.array([np.mean([scenario[s,g,a]['throughput']-scenario[s,g,b]['throughput'] for g in selected]) for s in seeds])
            ci=np.quantile(d[idx].mean(axis=1),[.025,.975])
            comparisons.append(dict(arm=a,baseline=b,regime=reg,days=len(d),delta_unserved_mean=d.mean(),median=np.median(d),
                                    ci_low=ci[0],ci_high=ci[1],wins=int(sum(d < -1e-6)),ties=int(sum(abs(d)<=1e-6)),
                                    losses=int(sum(d>1e-6)),mean_delta_conversion_loss=losses.mean(),mean_delta_throughput=cycling.mean()))
            byday.extend(dict(arm=a,baseline=b,regime=reg,seed=s,delta=d[i]) for i,s in enumerate(seeds))
    write_csv(out/'paired_effects.csv',comparisons);write_csv(out/'paired_days.csv',byday)
    c=cases[0];plain=np.array(runs[c['id'],'rule6']['actions']);mutants=[]
    for name,row,col,delta in [('bad_soc',3,4,1.),('unbalanced',12,0,1.),('terminal',23,4,-1.),('reserve',4,2,100.)]:
        test=plain.copy();test[row,col]+=delta
        v,_=inspect(c,params,test);assert v>1e-6;mutants.append(dict(name=name,residual=v))
    check=dict(policies=len(arms),cases=len(cases),trajectories=len(runs),hourly_actions=len(runs)*24,
               max_residual=residual,mutation_rejections=mutants,fallbacks=sum(x['fallback'] for x in outcomes))
    if repeat:
        rr=load_runs(repeat);assert rr.keys()==runs.keys()
        exact=0;maximum=0.;changed=[]
        for k,v in runs.items():
            x=np.array(v['actions']);y=np.array(rr[k]['actions']);m=float(abs(x-y).max())
            exact+=int(np.array_equal(x,y));maximum=max(maximum,m)
            if m>1e-6:changed.append(k)
        check['same_machine_repeat']=dict(exact_action_trajectories=exact,total=len(rr),max_difference=maximum,
                                           material_changes=changed)
    (out/'validation.json').write_text(json.dumps(check,indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--raw',type=Path,default=ROOT/'results/holdout.jsonl.gz')
    p.add_argument('--out',type=Path,default=ROOT/'results');p.add_argument('--repeat',type=Path)
    args=p.parse_args();run(args.raw,args.out,args.repeat)
