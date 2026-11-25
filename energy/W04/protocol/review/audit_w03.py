"""Read-only audit of W03 packet, without a solver dependency for recorded schedules.
Run: python audit_w03.py /path/to/W03 --output audit.json [--rerun-load]
The source model's builder is reused only for reconstructing LP coefficients; the
box Lagrangian is evaluated using Fraction. AC replay uses the delivered checker.
No Lean/MILP/UC solver rebuild is implied. The event-log analysis is retrospective.
"""
import argparse,csv,gzip,hashlib,importlib.util,json,math,platform,sys,types,subprocess
from collections import Counter,defaultdict
from fractions import Fraction as F
from pathlib import Path
from statistics import median
import numpy as np
import scipy

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def verify(root,rerun):
    count=0
    for line in (root/'SHA256SUMS.txt').read_text().splitlines():
        digest,rel=line.split(maxsplit=1); rel=rel.lstrip('*'); assert sha(root/rel)==digest,rel; count+=1
    design=json.loads((root/'protocol/design.json').read_text())
    # Use only the supplied, solver-free matrix assembly methods. No solver methods invoked.
    sys.path.insert(0,str(root/'src'))
    if importlib.util.find_spec('highspy') is None:
        sys.modules['highspy']=types.ModuleType('highspy')
    import common
    from battery_model import arrays,model
    from battery_audit import exact_box
    from ac import read_case,independent
    cases={x['id']:arrays(x) for x in json.loads((root/'inputs/battery_holdout.json').read_text())}
    rows=[json.loads(line) for line in gzip.open(root/'results/A/holdout.jsonl.gz','rt')]
    expected={(cid,m,i) for cid,a in cases.items() for m in design['A']['policies'] if m!='symmetry' or a['cohort']=='interchangeable' for i in range(3)}
    assert len(rows)==len(expected) and {(x['case'],x['policy'],x['repeat']) for x in rows}==expected
    outcomes=Counter(); ncheck=0; maxres=0.
    def check(a,p):
        c,d=np.array(p,dtype=float); e=a['initial'].copy(); prev=float(a['previous']); cost=0.; violation=0.
        for t in range(a['t']):
            g=float(a['load'][t]);
            for i in range(a['n']):
                ch,ds=c[i,t],d[i,t]; e[i]+=a['eta_c'][i]*ch-ds/a['eta_d'][i];g+=ch-ds
                lim=a['power'][i]*a['availability'][i,t]
                violation=max(violation,-ch,-ds,ch-lim,ds-lim,min(ch,ds),a['floor'][i,t]-e[i],e[i]-a['capacity'][i]);cost+=(ch+ds)*a['wear'][i]
            violation=max(violation,a['grid_lo'][t]-g,g-a['grid_hi'][t],abs(g-prev)-a['ramp']);cost+=g*a['price'][t];prev=g
        return float(cost),float(max(violation,np.max(np.abs(e-a['initial'])-a['terminal_tolerance'])))
    for r in rows:
        hit=r['target_time'] is not None
        if hit: assert r['target_time']<=2 and r['upper']-r['lower']<=2e-5+.001*max(1,abs(r['upper']))+1e-10
        outcomes[(r['policy'],r['case'])]+=int(hit)
        if r['repeat']!=0: continue
        obj,err=check(cases[r['case']],r['best_powers']);assert err<=2e-6 and abs(obj-r['upper'])<1e-5;maxres=max(maxres,err);ncheck+=1
        for s in r['steps']:
            if 'returned_powers' in s:
                obj,err=check(cases[r['case']],s['returned_powers']);assert (err<=2e-6)==s['returned_check']['valid'] and abs(obj-s['returned_check']['cost'])<1e-5;ncheck+=1
                if s['returned_check']['valid']:maxres=max(maxres,err)
    certs=json.loads((root/'results/A/exact_lp_certificates.json').read_text());assert len(certs)==24
    for c in certs:
        a=cases[c['case']];m,_,_=model(a,[[i] for i in range(a['n'])],'lp');assert str(exact_box(m,c['row_dual']))==c['exact_lower']
    forced=sorted(k for k,a in cases.items() if a['cohort']=='forced_opposition'); idx=defaultdict(list)
    for r in rows:idx[(r['case'],r['policy'])].append(r)
    def obj_at(r,dt):
        vals=[x['upper'] for x in r['events'] if 'upper' in x and (x['time']<=dt or x.get('source')=='fallback')];return min(vals)
    trajectory=[]
    for dt in [.05,.1,.25,.5,1.,2.]:
        rec={'seconds':dt}
        for m in ['full_milp','lp_recovery']:
            diffs=[median(obj_at(r,dt) for r in idx[(cid,'adaptive')])-median(obj_at(r,dt) for r in idx[(cid,m)]) for cid in forced]
            rec[m]={'better':sum(v< -1e-5 for v in diffs),'tie':sum(abs(v)<=1e-5 for v in diffs),'worse':sum(v>1e-5 for v in diffs),'case_differences':diffs}
        trajectory.append(rec)
    cr=json.loads((root/'results/C/runs.json').read_text());assert len(cr)==36
    for r in cr:
        case=read_case(root/'inputs/ac'/(r['case']+'.m'));v=[np.array(x) for x in r['variables']];q=independent(case,*v);assert q['valid'] and abs(q['cost']-r['check']['cost'])<1e-6;v[2][0]+=1;assert not independent(case,*v)['valid']
    E=json.loads((root/'inputs/load_forecasts.json').read_text());p=E['parameters'];lookup={a['id']:a for a in E['cases']};erows=json.loads((root/'results/E/runs.json').read_text());assert len(erows)==72
    hours=0
    for r in erows:
        a=lookup[r['case']];prev=p['previous'];e=p['initial'];loss=service=0.
        for t,(g,c,d,u,end) in enumerate(r['actions']):
            e+=p['eta_c']*c-d/p['eta_d'];lim=p['power']*a['available'][t];tol=1e-6
            assert abs(e-end)<tol and a['floor'][t]-tol<=e<=p['energy']+tol
            assert -tol<=g<=p['grid_cap']+tol and abs(g-prev)<=p['ramp']+tol
            assert -tol<=c<=lim+tol and -tol<=d<=max(0,lim-a['reserve'][t])+tol and min(c,d)<=tol
            assert abs(g+d-c+u-a['load'][t])<=tol and -tol<=u<=a['load'][t]-p['facility']+tol
            service+=a['load'][t]-p['facility']-u;loss+=c*(1-p['eta_c'])+d*(1/p['eta_d']-1);prev=g;hours+=1
        assert abs(service-r['useful_compute_MWh'])<1e-6 and abs(loss-r['conversion_loss_MWh'])<1e-6 and e>=95-tol
    def service_comparison(rs):
        lookup={(r['case'],r['method']):r for r in rs};ds={cid:lookup[(cid,'rolling_mpc')]['unserved_MWh']-lookup[(cid,'forecast_rule')]['unserved_MWh'] for cid in sorted({r['case'] for r in rs})};return {'additional_unserved_MWh':sum(ds.values()),'wins':sum(v< -1e-6 for v in ds.values()),'ties':sum(abs(v)<=1e-6 for v in ds.values()),'losses':sum(v>1e-6 for v in ds.values()),'differences':ds}
    results={'scope':'Archive integrity, recorded-schedule validation, exact rational box bounds, delivered AC checker, retrospective event-log reanalysis; not solver/Lean/UC rebuild.','manifest_files':count,'A_trials':len(rows),'A_schedules':ncheck,'A_max_accepted_residual':maxres,'exact_bounds':len(certs),'case_all_three_hit':{m:sum(n==3 for (mm,_),n in outcomes.items() if mm==m) for m in design['A']['policies']},'A_fixed_deadlines':trajectory,'C_checks':len(cr),'C_corruptions_rejected':len(cr),'E_hours':hours,'E_archived':service_comparison(erows),'environment':{'python':platform.python_version(),'platform':platform.platform(),'scipy':scipy.__version__,'numpy':np.__version__}}
    if rerun:
        from load_control import trial
        fresh=[trial(a,m) for a in E['cases'] for m in design['E']['methods']]
        original={(r['case'],r['method']):r for r in erows};differences=[{'case':r['case'],'method':r['method'],'old_unserved':original[(r['case'],r['method'])]['unserved_MWh'],'new_unserved':r['unserved_MWh']} for r in fresh if abs(original[(r['case'],r['method'])]['unserved_MWh']-r['unserved_MWh'])>1e-6]
        results['E_fresh']=service_comparison(fresh);results['E_fresh']['material_differences']=differences;results['E_fresh']['runs']=len(fresh);results['E_fresh']['fallback_hours']=sum(len(r['invalid_or_late_fallback_hours']) for r in fresh)
        # Retain full new schedules so the cross-platform run is auditable.
        results['E_fresh_runs']=fresh
    return results
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('root',type=Path);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--rerun-load',action='store_true');a=ap.parse_args();r=verify(a.root.resolve(),a.rerun_load);a.output.write_text(json.dumps(r,indent=2,default=lambda x:x.item() if isinstance(x,np.generic) else x.tolist())+'\n');print(json.dumps({k:v for k,v in r.items() if k not in ('E_fresh_runs','A_fixed_deadlines')},indent=2,default=lambda x:x.item() if isinstance(x,np.generic) else x.tolist()))
