"""Rebuild independently scored action and exact lower-certificate trajectories."""
import argparse
import csv
import gzip
import json
import math
import statistics
from collections import Counter, defaultdict
from fractions import Fraction as Q
from pathlib import Path
from engine import HERE, ARMS, CLOCKS, SEEDS, arrays, model, validate, direct, np, round_lower

def write(path,rows):
    if not rows:raise ValueError('Unexpected empty table: '+str(path))
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
def saved(path,value):
    path.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
def exact_replay(m,dual):
    # Independently traverse the sparse model by column and evaluate both corners explicitly.
    y=[Q(float(v)) for v in dual]
    if len(y)!=len(m.lhs):raise ValueError('row multiplier dimension')
    base=Q(0)
    for i,mult in enumerate(y):
        endpoint=m.lhs[i] if mult>0 else m.rhs[i]
        if not math.isfinite(endpoint):y[i]=Q(0)
        elif mult:base+=mult*Q(float(endpoint))
    col=[Q(float(v)) for v in m.cost]
    for i,j,value in zip(m.row,m.col,m.val):
        if y[i]:col[j]-=y[i]*Q(float(value))
    return base+sum(min(q*Q(float(l)),q*Q(float(h))) for q,l,h in zip(col,m.lo,m.hi) if q)
def compact(cases,ids,measure):
    a=np.array([cases[i][measure] for i in ids if cases[i][measure] is not None])
    return float(np.median(a)) if len(a) else None
def analyze(raw,out):
    out.mkdir(parents=True,exist_ok=True)
    with gzip.open(HERE/'protocol/instances.json.gz','rt') as f:cases={a['id']:arrays(a) for a in json.load(f)}
    with gzip.open(raw,'rt') as f:rr=[json.loads(line) for line in f]
    keys={(r['case'],r['arm'],r['repeat']) for r in rr}
    assert keys=={(i,b,k) for i in cases for b in ARMS for k in range(3)} and len(keys)==len(rr)==900
    allbounds={};models={};memo={};counts=Counter();worst=0.
    for r in rr:
        i=r['case'];a=cases[i]
        if i not in models:models[i]=model(a,[[j] for j in range(a['n'])],'lp')[0]
        for v in r['witnesses']:
            c,d=np.asarray(v['c']),np.asarray(v['d'])
            assert np.isfinite(c).all() and np.isfinite(d).all()
            cost,vi=direct(a,(c,d))
            assert (vi<=2e-6)==v['valid'] and abs(cost-v['cost'])<=1e-5
            counts['reviewed_primal']+=1
            counts['rejected_primal']+=int(not v['valid'])
            if v['valid']:worst=max(worst,vi)
        for c in r['certificates']:
            k=(i,tuple(c['dual']))
            if k not in memo:memo[k]=exact_replay(models[i],c['dual'])
            q=memo[k];assert str(q)==c['fraction'] and round_lower(q)==c['lower']
            counts['exact_evaluations_rechecked']+=1
            allbounds[i]=max(allbounds.get(i,-math.inf),round_lower(q))
    trial=[];stages=[];group=defaultdict(list);controls=[]
    for i,a in cases.items():
        m=models[i];bad=[0.]*len(m.lhs);bad[0]=1.
        baseline=exact_replay(m,bad)
        assert Q(round_lower(baseline))<=baseline
        badpow=np.zeros((a['n'],a['t']));badpow[0,0]=2*a['power'][0]+1
        assert direct(a,(badpow,0*badpow))[1]>2e-6
        if a['fallback_supplied']:
            c0,er=direct(a,(a['fallback_charge'],a['fallback_discharge']))
            assert er<=2e-6
            if i in allbounds:assert allbounds[i]<=c0+2e-5
        controls.append(dict(case=i,power_corruption_rejected=True,positive_illegal_row_multiplier_clipped=bool(math.isinf(m.lhs[0])),
                             fallback_replay=bool(a['fallback_supplied'])))
    for r in rr:
        a=cases[r['case']];events=r['events'];U=L=None;tt=None;first=None;source=None
        numerical=None
        for e in events:
            assert 0<=e['at']<=2.
            if 'U' in e:
                w=r['witnesses'][e['witness']];assert w['valid'] and w['cost']==e['U'] and w['at']==e['at']
                U=e['U'];source=e['stage'];first=e['at'] if first is None else first
                if r['case'] in allbounds:assert U>=allbounds[r['case']]-2e-5
            else:
                L=e['L'];assert any(c['lower']==L and c['at']==e['at'] for c in r['certificates'])
            if U is not None and L is not None and U-L<=.00002+.001*max(1,abs(U)) and tt is None:tt=e['at']
        assert tt==r['target']
        for s in r['stages']:
            if s.get('numerical_native_lower') is not None and s['return_time']<=2:numerical=s['numerical_native_lower']
            log=s.get('log','')
            stages.append(dict(case=r['case'],arm=r['arm'],repeat=r['repeat'],stage=s['label'],status=s.get('status'),start=s['start'],end=s.get('end'),
                               build_s=s.get('build_s'),solve_s=s.get('solve_with_callbacks_s'),validation_s=s.get('validation_s'),
                               certificate_s=s.get('certificate_s'),transfer_s=s.get('transfer_s'),start_source=s.get('transfer_source'),
                               confirmed_start=s.get('confirmed_start'),nodes=s.get('nodes'),iterations=s.get('lp_iterations'),
                               presolve_in_log='presolv' in log.lower(),explicit_lp_before_native=s['label']=='native' and any(z['label']=='outer_lp' for z in r['stages'])))
        common=allbounds.get(r['case']);fb=r['fallback_cost'];area=None;reason=''
        if fb is None:reason='no_supplied_fallback'
        elif common is None:reason='no_usable_offline_certificate'
        elif fb-common<=1e-10:reason='zero_or_tolerance_span'
        else:
            last=0.;cur=fb;total=0.
            for e in events:
                if 'U' in e:
                    total+=(e['at']-last)*(cur-common);cur=e['U'];last=e['at']
            area=(total+(2-last)*(cur-common))/(2*(fb-common))
        valid_numeric=(U is not None and numerical is not None and numerical<=U+2e-5 and U-numerical<=.00002+.001*max(1,abs(U)))
        offhit=(U is not None and common is not None and U-common<=.00002+.001*max(1,abs(U)))
        row=dict(case=r['case'],seed=r['seed'],family=r['cohort'],size=f"{a['n']}x{a['t']}",supplied=r['supplied'],arm=r['arm'],repeat=r['repeat'],
                 ontime_hit=tt is not None,t_target=tt,capped_time=tt if tt is not None else 2.,first_action=first,final_U=U,final_L=L,
                 offline_L=common,area=area,area_missing_reason=reason,final_source=source,retained_fallback=source=='fallback',
                 wall_s=r['wall'],synchronous_hit=tt is not None and r['wall']<=2,overrun=r['wall']>2,
                 native_numerical_hit=bool(valid_numeric),offline_hit=bool(offhit),no_action=U is None)
        for clock in CLOCKS:
            row['U_'+str(clock)]=min((e['U'] for e in events if e['at']<=clock and 'U'in e),default=None)
        trial.append(row);group[r['case'],r['arm']].append(row)
    write(out/'trials.csv',trial);write(out/'stages.csv',stages);write(out/'mutation_controls.csv',controls)
    case_rows=[];lookup={}
    for (i,arm),rows in group.items():
        a=cases[i];q=dict(case=i,seed=a['seed'],family=a['cohort'],size=f"{a['n']}x{a['t']}",arm=arm,supplied=a['fallback_supplied'],
            all_hit=all(z['ontime_hit'] for z in rows),all_available=all(not z['no_action'] for z in rows),
            all_offline_hit=all(z['offline_hit'] for z in rows),all_native_numerical_hit=all(z['native_numerical_hit'] for z in rows),
            all_synchronous=all(z['synchronous_hit'] for z in rows))
        for key in ['capped_time','area','first_action']+['U_'+str(c) for c in CLOCKS]:
            vals=[z[key] for z in rows if z[key] is not None];q[key]=statistics.median(vals) if len(vals)==3 else None
        case_rows.append(q);lookup[i,arm]=q
    write(out/'case_medians.csv',case_rows)
    contrasts=[];effects=[];rng=np.random.default_rng(5171);resamples=rng.integers(0,len(SEEDS),(5000,len(SEEDS)))
    for comp in ['native_cert','lp_repair','lp_only','native_unmetered_certificate']:
        for key in ['all_hit','all_available','capped_time','area','first_action','all_offline_hit']+['U_'+str(c) for c in CLOCKS]:
            blocks=defaultdict(list);ds=[];wins=ties=losses=missing=0
            for i,a in cases.items():
                u=lookup[i,'screen'][key];b=lookup[i,comp][key]
                difference=None if u is None or b is None else float(u)-float(b)
                if difference is None:missing+=1
                else:
                    fb=group[i,'screen'][0]['fallback_cost']
                    scale=abs(fb) if fb is not None else sum(abs(a['load']*a['price']))
                    tol=.001*max(1,scale) if key.startswith('U_') else 1e-8
                    benefit=difference if key.startswith('all_') else -difference
                    wins+=benefit>tol;losses+=benefit< -tol;ties+=abs(benefit)<=tol
                    ds.append(difference);blocks[a['seed']].append(difference)
                effects.append(dict(case=i,seed=a['seed'],family=a['cohort'],baseline=comp,metric=key,screen=u,reference=b,delta=difference))
            func=np.mean if key.startswith('all_') else np.median
            boot=[]
            for draw in resamples:
                vals=[v for x in draw for v in blocks[SEEDS[x]]]
                if vals:boot.append(func(vals))
            ci=np.quantile(boot,[.025,.975]) if boot else [None,None]
            contrasts.append(dict(baseline=comp,metric=key,pairs=len(ds),missing=missing,mean_delta=np.mean(ds) if ds else None,
                             median_delta=np.median(ds) if ds else None,ci_low=ci[0],ci_high=ci[1],wins=wins,ties=ties,losses=losses))
    write(out/'paired_cases.csv',effects);write(out/'contrasts.csv',contrasts)
    summary=[]
    for arm in ARMS:
        for stratum in ['all']+list(dict.fromkeys(v['cohort'] for v in cases.values()))+['supplied','absent']:
            r=[x for x in case_rows if x['arm']==arm and (stratum=='all' or x['family']==stratum or
                stratum=='supplied' and x['supplied'] or stratum=='absent' and not x['supplied'])]
            subset=[x for x in trial if x['case'] in {z['case'] for z in r} and x['arm']==arm];times=[z['wall_s'] for z in subset]
            summary.append(dict(arm=arm,stratum=stratum,cases=len(r),all_repeat_target=sum(z['all_hit'] for z in r),
                all_repeat_action=sum(z['all_available'] for z in r),all_repeat_synchronous=sum(z['all_synchronous'] for z in r),
                all_offline_hit=sum(z['all_offline_hit'] for z in r),all_native_numerical_hit=sum(z['all_native_numerical_hit'] for z in r),
                trials=len(subset),overruns=sum(z['overrun'] for z in subset),no_action=sum(z['no_action'] for z in subset),
                fallback_only=sum(z['retained_fallback'] for z in subset),wall_median=np.median(times),wall_p95=np.quantile(times,.95),wall_max=max(times)))
    write(out/'summary.csv',summary)
    saved(out/'verification.json',dict(expected_cases=60,expected_trials=900,actual_trials=len(rr),**counts,
          unique_dual_vectors=len(memo),cases_with_common_reference=len(allbounds),max_valid_primal_residual=worst,
          negative_power_controls=len(controls),clipped_illegal_multiplier_controls=sum(x['positive_illegal_row_multiplier_clipped'] for x in controls)))
if __name__=='__main__':
    cli=argparse.ArgumentParser();cli.add_argument('--raw',type=Path,required=True);cli.add_argument('--out',type=Path,required=True)
    args=cli.parse_args();analyze(args.raw,args.out)
