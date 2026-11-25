"""Re-evaluate every solution, matched comparison, and native backend profile."""
import argparse,csv,gzip,json,re,statistics,sys
from collections import Counter
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
W04=HERE.parents[1]/'W04'
sys.path.insert(0,str(W04/'C'))
from review_check import get_network
ARMS=['full_dc','full_matched','all','degree','guided']
def table(path,rows):
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
def med(values):
    data=[x for x in values if x is not None]
    return statistics.median(data) if data else None
def summarize(raw,out,profile):
    out.mkdir(parents=True,exist_ok=True);rows=[];cells=[];pairs=[];profiles=[]
    expected=0;on=0;feasible=0;corrupt=0;delta=0.
    for case in sorted((HERE/'inputs').glob('*.m')):
        mode=case.stem;bus,gen,br,gb,fr,to,base,powers,verify=get_network(case)
        costtext=case.read_text().split('mpc.gencost')[1].split('];')[0]
        local=[]
        for rep in range(5):
            for arm in ARMS:
                f=raw/f'{mode}_{arm}_{rep}.json';r=json.loads(f.read_text())
                assert (r['case'],r['policy'],r['repeat'])==(mode,arm,rep)
                expected+=1;ok=False;hit=False;cost=None
                if 'variables' in r:
                    x=[np.array(v) for v in r['variables']];v=verify(*x)
                    assert v['valid']==r['check']['valid'] and abs(v['cost']-r['check']['cost'])<1e-6
                    ok=v['valid'];hit=ok and r['elapsed']<=12;cost=v['cost']
                    feasible+=ok;on+=hit
                    if ok:
                        x[2][0]+=1
                        assert not verify(*x)['valid'] and r['corrupt_rejected'];corrupt+=1
                    delta=max(delta,r['start_lift_mismatch'])
                st=r.get('structure',{});nt=r.get('native_timing',{})
                row=dict(case=mode,arm=arm,rep=rep,valid=ok,hit=hit,cost=cost,elapsed=r.get('elapsed'),status=r.get('status',r.get('error','')),
                         pivots=len(r.get('pivots',{})),selection_s=r.get('selection_s'),build_s=r.get('build_seconds'),validation_s=r.get('validation_s'),
                         iterations=r.get('iterations'),n=r.get('n_variables'),m=r.get('constraint_rows'),jac=r.get('jacobian_nnz'),
                         hess=st.get('hessian_nnz'),fill=st.get('added_lower_fill'),cond=st.get('condition_1_est'),regularized_factor_s=st.get('proxy_factor_s'),
                         ipopt_pd_wall_s=nt.get('PDSystemSolverTotal',{}).get('wall_s'),rss_bytes=r.get('rss_bytes'),
                         lower=r.get('lower'),missing_lower=r.get('lower_unavailable',''))
                rows.append(row);local.append(row)
        for arm in ARMS:
            group=[x for x in local if x['arm']==arm];sample=group[0]
            cells.append(dict(case=mode,arm=arm,buses=len(bus),generators=len(gen),excess_colocations=len(gb)-len(set(gb)),n=sample['n'],m=sample['m'],
                hess=sample['hess'],jac=sample['jac'],fill=sample['fill'],cond_proxy=sample['cond'],pivots=sample['pivots'],
                hits=sum(x['hit'] for x in group),valid=sum(x['valid'] for x in group),cost=med(x['cost'] for x in group if x['hit']),
                ontime_median_s=med(x['elapsed'] for x in group if x['hit']),all_returns_median_s=med(x['elapsed'] for x in group)))
        for comp in ['full_matched','full_dc','all','degree']:
            ratios=[];relative=[]
            for rep in range(5):
                a=next(x for x in local if x['rep']==rep and x['arm']=='guided');b=next(x for x in local if x['rep']==rep and x['arm']==comp)
                if a['hit'] and b['hit']:
                    diff=abs(a['cost']-b['cost'])/max(1,abs(b['cost']))
                    if diff<=1e-5:ratios.append(a['elapsed']/b['elapsed']);relative.append(diff)
            ah=sum(x['hit'] for x in local if x['arm']=='guided');bh=sum(x['hit'] for x in local if x['arm']==comp)
            pairs.append(dict(case=mode,comparator=comp,matched=len(ratios),time_ratios=json.dumps(ratios),ratio=med(ratios),
                              max_relative_cost=max(relative,default=None),guided_hits=ah,baseline_hits=bh,
                              practical=bool(ratios and med(ratios)<=.9 and ah>=bh)))
        if profile:
            for arm in ARMS:
                name=mode+'_'+arm;run=json.loads((profile/(name+'.run.json')).read_text());f=profile/(name+'.json')
                pf=json.loads(f.read_text()) if f.exists() else {}
                with gzip.open(profile/(name+'.native.gz'),'rt',errors='replace') as stream:logs=stream.read()
                def numbers(pat):return [float(x.replace('D','E')) for x in re.findall(pat,logs)]
                times=numbers(r'Elapsed time for factorization\s*=\s*([\d.ED+\-]+)')
                ops=numbers(r'Operations in node elimination\s*=\s*([\d.ED+\-]+)')
                entries=numbers(r'INFOG\(29\)\s+Number of entries in factors\s*=\s*([\d.ED+\-]+)')
                valid=False
                if 'variables' in pf:
                    v=verify(*[np.array(a) for a in pf['variables']]);valid=v['valid'];assert valid==pf['check']['valid']
                profiles.append(dict(case=mode,arm=arm,process_exit=run['exit'],watchdog=run['watchdog'],valid=valid,
                    hit60=bool(valid and pf['elapsed']<=60),elapsed=pf.get('elapsed'),status=pf.get('status'),cost=pf.get('check',{}).get('cost'),
                    factor_times_logged=len(times),factor_op_reports=len(ops),factor_entry_reports=len(entries),
                    mumps_factor_wall_s=sum(times) if times else None,reported_node_elimination_ops=sum(ops) if ops else None,
                    max_numeric_factor_entries=max(entries,default=None)))
    assert expected==125
    table(out/'trials.csv',rows);table(out/'cases.csv',cells);table(out/'matched.csv',pairs)
    if profile:table(out/'native_profile.csv',profiles)
    rec=dict(scheduled=expected,valid=feasible,ontime=on,corruptions=corrupt,max_initial_lift_mismatch=delta,
             by_arm={a:sum(row['hit'] for row in rows if row['arm']==a) for a in ARMS},
             qualified_practical_by_comparator={a:sum(row['practical'] for row in pairs if row['comparator']==a) for a in ['full_matched','full_dc','all','degree']},
             profiles=len(profiles),profile_hits=sum(x['hit60'] for x in profiles))
    (out/'verification.json').write_text(json.dumps(rec,indent=2)+'\n')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('raw',type=Path);p.add_argument('output',type=Path);p.add_argument('--profile',type=Path)
    q=p.parse_args();summarize(q.raw,q.output,q.profile)
