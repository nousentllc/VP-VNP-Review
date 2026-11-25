"""Independent physical replay and locked clustered comparisons for W05-E."""
import argparse,csv,gzip,json,math
from collections import defaultdict
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parent
def read(path):
    p=Path(path)
    return json.loads(gzip.decompress(p.read_bytes()) if p.suffix=='.gz' else p.read_bytes())

def write(path,rows):
    if not rows:return
    fields=list(dict.fromkeys(k for r in rows for k in r))
    with Path(path).open('w',newline='') as f:
        w=csv.DictWriter(f,fields);w.writeheader();w.writerows(rows)
def save(path,x):
    Path(path).write_text(json.dumps(x,indent=2,allow_nan=False,default=lambda z:z.item())+'\n')

def measure(c,a,p):
    x=np.array(a,float)
    if x.shape!=(24,5) or not np.isfinite(x).all():raise ValueError("shape or finite")
    g,ch,d,u,e=x.T;load=np.array(c['load']);av=np.array(c['available'],float);reserve=np.array(c['reserve'])
    rate=np.diff(np.r_[p['previous'],g]);floor=np.array(c['floor'])
    gaps=dict(balance=np.max(abs(g+d-ch+u-load)),energy=np.max(abs(e-p['initial']-np.cumsum(ch*p['eta_c']-d/p['eta_d']))),
              nonnegative=-np.min(x),rate=np.max(abs(rate))-p['ramp'],cap=np.max(g)-p['grid_cap'],charge=np.max(ch-av*p['power']),
              discharge=np.max(d-np.maximum(0.,av*p['power']-reserve)),exclusive=np.max(np.minimum(ch,d)),
              protected=np.max(u-load+p['facility']),energy_floor=np.max(floor-e),energy_cap=np.max(e)-p['energy'],
              terminal=p['initial']-e[-1])
    t=np.arange(24)
    values=dict(shed=float(sum(u)),served=float(sum(load-p['facility']-u)),imports=float(sum(g)),terminal=float(e[-1]),
                throughput=float(sum(ch+d)),loss=float(sum((1-p['eta_c'])*ch+(1/p['eta_d']-1)*d)),
                peak=float(max(g)),worst_hour=float(max(u)),unavailable_reserve=float(sum(reserve*(1-av))),
                min_floor=float(min(e-floor)),max_residual=max(0.,max(gaps.values())),
                purchase_flat=50.*sum(g),purchase_peak=sum(g*np.where((t>=16)&(t<=21),120,30)),
                purchase_solar=sum(g*np.where((t>=10)&(t<=15),-20,70)))
    return values,gaps

def quant(x,q):return float(np.quantile(x,q))
def upper_tail(x):
    k=max(1,int(math.ceil(x.shape[-1]*.10)))
    return np.mean(np.sort(x,axis=-1)[...,-k:],axis=-1)

def bootstrap(group,by,pair,reg,rng):
    keys=sorted({r['seed'] for r in group});a,b=pair
    regs=['base','biased_forecast','outage_reserve'] if reg=='all' else [reg]
    if any((s,v,z) not in by for s in keys for v in regs for z in pair):
        return dict(arm=a,comparator=b,regime=reg,complete=False),[],[]
    def vals(m):
        return np.array([[np.mean([by[s,v,arm][m] for v in regs]) for arm in pair] for s in keys])
    d=vals('shed');delta=d[:,0]-d[:,1];f=vals('fallback_fraction');fb=f[:,0]-f[:,1]
    boot=rng.integers(0,len(keys),size=(10000,len(keys)));effect=delta[boot].mean(1)
    risk=upper_tail(d[boot,0])-upper_tail(d[boot,1])
    upper=quant(effect,.975);risk_up=quant(risk,.975);fb_up=quant(fb[boot].mean(1),.975)
    exact_safe=all(by[s,v,arm]['max_residual']<=1e-6 for s in keys for v in regs for arm in pair)
    cover=np.max(abs(np.diff(vals('unavailable_reserve'),axis=1)))<1e-7
    good=bool(exact_safe and cover and risk_up<=5. and fb_up<=.005)
    row=dict(arm=a,comparator=b,regime=reg,complete=True,seeds=len(keys),mean_delta_shed=delta.mean(),median_delta_shed=np.median(delta),
             l95=quant(effect,.025),u95=upper,lower_days=sum(delta<-1e-6),tied_days=sum(abs(delta)<=1e-6),
             higher_days=sum(delta>1e-6),d_cvar90=upper_tail(d[:,0])-upper_tail(d[:,1]),cvar_u975=risk_up,
             d_fallback_fraction=fb.mean(),fallback_u975=fb_up,reliability_noninferior=good,gate_pass=bool(good and upper<-.1))
    for key in ('served','imports','loss','throughput','terminal','peak','worst_hour','decision_seconds','unavailable_reserve'):
        v=vals(key);row['delta_'+key]=np.mean(v[:,0]-v[:,1])
    days=[dict(arm=a,comparator=b,regime=reg,seed=s,delta_shed=delta[i],arm_shed=d[i,0],comparator_shed=d[i,1],delta_fallback_fraction=fb[i]) for i,s in enumerate(keys)]
    econ=[]
    if reg=='all':
        for price in ['flat','peak','solar']:
            v=vals('purchase_'+price);dp=float(np.mean(v[:,0]-v[:,1]));ds=row['delta_served']
            for wear in (0,10):
                for fixed in (0,10):
                    wearcost=wear*row['delta_throughput'];term=50*row['delta_terminal']
                    compute=.2*row['delta_decision_seconds']/3600
                    intercept=-dp-wearcost+term-compute-fixed
                    direction='above' if ds>1e-8 else 'below' if ds< -1e-8 else 'constant'
                    econ.append(dict(arm=a,comparator=b,price=price,wear_USD_per_MWh=wear,incremental_fixed_USD_day=fixed,
                        delta_served_MWh=ds,delta_purchase_USD=dp,delta_wear_USD=wearcost,delta_terminal_USD=term,
                        delta_computing_USD=compute,net_intercept_USD=intercept,service_value_direction_for_positive_net=direction,
                        break_even_USD_per_served_MWh=-intercept/ds if direction!='constant' else None))
    return row,days,econ

def run(primary,out,repeat=None):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    inp=read(ROOT/'inputs/holdout.json.gz');p=inp['parameters'];cases={c['id']:c for c in inp['cases']}
    cfg=read(ROOT/'protocol/development.json')['cfg'];lock=read(ROOT/'protocol/freeze.json')
    expected={(cid,arm) for cid in cases for arm in lock['arms']};seen=set();errors=[];rows=[];test_controls={}
    max_diff=0.;changed=[];repeats=0;witness=defaultdict(list)
    accuracy=defaultdict(list)
    for c in cases.values():
        for h,issue in enumerate(c['issues']):
            idx=np.array(issue['valid']);leads=idx-h
            assert np.array_equal(idx,np.arange(h,min(h+12,24)))
            assert np.all(np.array(issue['available'])==np.where(leads<=1,np.array(c['available'])[idx],True))
            assert abs(issue['load'][0]-c['load'][h])<1e-10
            if len(idx)>6:
                actual=np.array(c['load'])[idx[6:]]
                accuracy[c['panel']].append(np.column_stack((np.array(issue['load'])[6:]-actual,issue['load'][5]-actual)))
    rep=gzip.open(repeat,'rt') if repeat else None
    with gzip.open(primary,'rt') as f:
        for line in f:
            r=json.loads(line);key=r['case'],r['arm'];c=cases[r['case']]
            if key in seen or key not in expected:raise ValueError(key)
            seen.add(key);rep_row=json.loads(next(rep)) if rep else None
            if rep and (rep_row['case'],rep_row['arm'])!=key:raise ValueError("replay order")
            if 'error' in r:
                errors.append([*key,r['error']]);continue
            m,gaps=measure(c,r['actions'],p)
            err=m['max_residual']
            if err>1e-6:errors.append([*key,'constraint',float(err)])
            d=r['decisions'];fb=[q['reason'] is not None for q in d];late=[q['clock_fallback'] for q in d]
            m.update(case=c['id'],arm=r['arm'],regime=c['regime'],seed=c['seed'],panel=c['panel'],
                fallback_count=sum(fb),fallback_fraction=np.mean(fb),deadline_count=sum(late),
                decision_seconds=sum(z['ready_seconds'] for z in d),largest_candidate_s=max(z['ready_seconds'] for z in d),
                largest_fallback_ready_s=max(z['safe_seconds'] for z in d),offline_solve_s=r['offline_seconds'],
                short_selections=sum(q['used']<q['info'] for q in d),
                fallback_solver_error_count=sum(q['reason'] is not None and q['reason']!='deadline' for q in d),
                safe_ready_misses=sum(q['safe_seconds']>p['online_deadline'] for q in d))
            rows.append(m)
            if rep:
                repeats+=1
                if 'error' in rep_row:changed.append([*key,rep_row['error']]);continue
                diff=np.max(np.abs(np.array(r['actions'])-rep_row['actions']));max_diff=max(max_diff,diff)
                if diff>0:changed.append([*key,float(diff)])
            if not test_controls:
                base=np.array(r['actions'])
                for name,(t,k,off) in {'balance':(0,0,1.),'soc':(1,4,1.),'terminal':(23,4,-100.),
                                      'reserve/power':(1,2,100.),'coincident':(1,1,100.)}.items():
                    mut=base.copy();mut[t,k]+=off
                    test_controls[name]=measure(c,mut,p)[0]['max_residual']
    if rep:
        if next(rep,None) is not None:raise ValueError('extra replay records')
        rep.close()
    assert seen==expected and all(x>1e-6 for x in test_controls.values())
    write(out/'scenario_metrics.csv',rows)
    arms=lock['arms'];pairs=[]
    for h in (3,6,12):
        for b in (f'rule{h}',f'none{h}',f'w04{h}'):pairs.append((f'learned{h}',b))
    pairs.extend([('learned12',cfg['strongest12']),('adaptive','fixed12'),('adaptive',cfg['strongest12']),
                  ('learned12','nested6'),('learned12','flat12'),('nested6','learned6'),('rule12','nestedrule6'),
                  ('w046','legacyrule6'),('w0412','legacyrule12'),('learned6','legacyrule6'),('learned12','legacyrule12')])
    # Eligible development winners may coincide with an earlier contrast.
    pairs=[v for v in dict.fromkeys(pairs) if v[0]!=v[1]]
    effects=[];all_days=[];econ=[];risk_tables=[];counts=[]
    for panel in ('primary','alternative'):
        sub=[r for r in rows if r['panel']==panel]
        by={(r['seed'],r['regime'],r['arm']):r for r in sub}
        seeds=lock[panel]
        for pair in pairs:
            for reg in ('all','base','biased_forecast','outage_reserve'):
                result,days,cost=bootstrap([{'seed':s} for s in seeds],by,pair,reg,np.random.default_rng(509051))
                result.update(panel=panel,confirmatory=(panel=='primary' and reg=='all' and pair in [('learned6','rule6'),('learned12',cfg['strongest12'])]))
                effects.append(result)
                for d in days:d['panel']=panel
                for e in cost:e['panel']=panel
                all_days+=days;econ+=cost
        for arm in arms:
            rr=[r for r in sub if r['arm']==arm]
            if not rr:continue
            for reg in ('all','base','biased_forecast','outage_reserve'):
                subset=[r for r in rr if reg=='all' or r['regime']==reg]
                if not subset:continue
                day=[np.mean([r['shed'] for r in subset if r['seed']==s]) for s in seeds if any(r['seed']==s for r in subset)]
                row=dict(panel=panel,arm=arm,regime=reg,scenario_days=len(subset),latent_days=len(day),cvar90=upper_tail(np.asarray(day)),
                    worst_day=max(r['shed'] for r in subset),worst_hour=max(r['worst_hour'] for r in subset),
                    min_terminal=min(r['terminal'] for r in subset),max_peak=max(r['peak'] for r in subset),
                    total_fallback=sum(r['fallback_count'] for r in subset),max_residual=max(r['max_residual'] for r in subset),
                    max_decision_seconds=max(r['largest_candidate_s'] for r in subset))
                for m in ['shed','served','imports','loss','throughput','terminal','peak','unavailable_reserve','decision_seconds']:
                    row['mean_'+m]=np.mean([r[m] for r in subset])
                risk_tables.append(row)
            for r in rr:
                off=by.get((r['seed'],r['regime'],'offline'))
                if off and r['shed']<off['shed']-1e-6:errors.append([r['case'],arm,'below offline reference'])
        en=np.vstack(accuracy[panel]);counts.append(dict(panel=panel,overlapping_leads=len(en),issued_MAE=np.mean(abs(en[:,0])),
            flat_MAE=np.mean(abs(en[:,1])),issued_RMSE=np.sqrt(np.mean(en[:,0]**2)),flat_RMSE=np.sqrt(np.mean(en[:,1]**2))))
    write(out/'effects.csv',effects);write(out/'paired_days.csv',all_days);write(out/'economics.csv',econ)
    write(out/'arm_summary.csv',risk_tables);write(out/'forecast_errors.csv',counts)
    save(out/'validation.json',dict(expected=len(expected),present=len(seen),physical_trajectories=len(rows),errors=errors,
             hourly_actions=len(rows)*24,max_residual=max(r['max_residual'] for r in rows),negative_controls=test_controls,
             total_fallback=sum(r['fallback_count'] for r in rows),total_late=sum(r['deadline_count'] for r in rows),
             solver_error_count=sum(r['fallback_solver_error_count'] for r in rows),fallback_ready_misses=sum(r['safe_ready_misses'] for r in rows),
             max_fallback_ready_seconds=max(r['largest_fallback_ready_s'] for r in rows),
             max_candidate_clock_seconds=max(r['largest_candidate_s'] for r in rows),
             schedule_replays=repeats,nonidentical_schedules=changed,max_replay_action_difference=max_diff))
    if errors:print('Scoring issues recorded in validation.json',flush=True)
if __name__=='__main__':
    pa=argparse.ArgumentParser();pa.add_argument('--primary',type=Path,required=True);pa.add_argument('--repeat',type=Path)
    pa.add_argument('--out',type=Path,required=True);v=pa.parse_args();run(v.primary,v.out,v.repeat)
