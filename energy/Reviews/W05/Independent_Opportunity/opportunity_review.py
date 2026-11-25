"""Independent CRGC W05 service and illustrative economic opportunity review.
Run: python opportunity_review.py /path/W05_Energy_Experiments.zip /path/output.json
Requires numpy and scipy. Does not execute or modify the original archive.
"""
from fractions import Fraction as F
from collections import defaultdict
from pathlib import Path
import gzip, json, sys, zipfile, hashlib
import numpy as np
from scipy.optimize import linprog
from scipy.sparse import lil_matrix

BASE = "Energy_Explorations/W05/"
def q(v): return F(float(v))
def pair(v): return F(*v)
def read_json(z, path): return json.loads(gzip.decompress(z.read(BASE+path)))
def mat(rows, n):
    m=lil_matrix((len(rows),n))
    for i,row in enumerate(rows):
        for j,v in row.items(): m[i,j]=float(v)
    return m.tocsr()

def model(c,p):
    eq=[];rhs=[];ine=[];irhs=[];boxes=[]
    ec=q(p['eta_c']); ed=q(1/p['eta_d']); rr=q(p['ramp'])
    for t in range(24):
        g,ch,ds,u,s=range(5*t,5*t+5)
        eq += [{g:1,ch:-1,ds:1,u:1},
               {s:1,ch:-ec,ds:ed,**({s-5:-1} if t else {})}]
        rhs += [q(c['load'][t]),q(p['initial']) if not t else F(0)]
        row={g:1,**({g-5:-1} if t else {})}
        ine += [row,{j:-v for j,v in row.items()}]
        irhs += [rr+(q(p['previous']) if not t else 0),
                  rr-(q(p['previous']) if not t else 0)]
        av=q(p['power'])*bool(c['available'][t])
        boxes += [(F(0),q(p['grid_cap'])),(F(0),av),
                  (F(0),max(F(0),av-q(c['reserve'][t]))),
                  (F(0),q(c['load'][t]-p['facility'])),
                  (q(c['floor'][t]),q(p['energy']))]
    return eq,rhs,ine,irhs,boxes

def dual_lower(cost,eq,rhs,ine,irhs,box,y,z):
    assert len(y)==len(eq) and len(z)==len(ine)
    assert all(v<=0 for v in z)
    red=list(cost); const=F(0)
    for d,row,b in zip(y+z,eq+ine,rhs+irhs):
        const+=d*b
        for j,c in row.items():red[j]-=d*c
    return const+sum(min(l*a,u*a) for (l,u),a in zip(box,red))

def check_primal(x,eq,rhs,ine,irhs,box):
    assert all(sum(v*x[j] for j,v in row.items())==b for row,b in zip(eq,rhs))
    assert all(sum(v*x[j] for j,v in row.items())<=b for row,b in zip(ine,irhs))
    assert all(l<=v<=u for v,(l,u) in zip(x,box))
    assert all(x[t+1]*x[t+2]==0 for t in range(0,120,5))

def review(zip_path):
    results=[];integrity={}
    with zipfile.ZipFile(zip_path) as z:
        for v in ('W04','W05'):
            b='Energy_Explorations/'+v+'/'
            lines=z.read(b+'SHA256SUMS.txt').decode().splitlines()
            for line in lines:
                h,f=line.split(maxsplit=1)
                assert hashlib.sha256(z.read(b+f.lstrip('*'))).hexdigest()==h
            integrity[v]=len(lines)
        panel=read_json(z,'E/inputs/holdout.json.gz')
        certs=read_json(z,'E/results/analysis/opportunity_certificates.json.gz')
        by={r['case']:r for r in certs}; p=panel['parameters']
        assert len(by)==len(certs)==len(panel['cases'])
        for c in panel['cases']:
            r=by[c['id']]; eq,rhs,ine,irhs,boxes=model(c,p)
            x=[pair(v) for t in r['primal'] for v in t]
            check_primal(x,eq,rhs,ine,irhs,boxes)
            cost=[F(j%5==3) for j in range(120)]
            low=dual_lower(cost,eq,rhs,ine,irhs,boxes,
                           [pair(v) for v in r['eq_multipliers']],
                           [pair(v) for v in r['le_multipliers']])
            upper=sum(x[3::5])
            assert (low,upper,upper-low)==(pair(r['lower']),pair(r['upper']),pair(r['gap']))
            item=dict(case=c['id'],panel=c['panel'],seed=c['seed'],regime=c['regime'],
                      service_gap=float(upper-low),service_exact_zero=upper==low,baseline_shed=float(upper))
            # Exact same HOURLY service in both comparisons; not an increased-service optimization.
            b=boxes.copy()
            for i in range(3,120,5):b[i]=(x[i],x[i])
            coef=[F([50,10,10,0,0][i%5]) for i in range(120)];coef[-1]=-50
            base_value=sum(a*v for a,v in zip(coef,x))
            ae=mat(eq,120); ai=mat(ine,120)
            for mode in ('same_stock','min_stock'):
                bb=b.copy()
                if mode=='same_stock':bb[-1]=(x[-1],x[-1])
                res=linprog(np.array(coef,dtype=float),A_eq=ae,b_eq=list(map(float,rhs)),
                            A_ub=ai,b_ub=list(map(float,irhs)),
                            bounds=[(float(l),float(u)) for l,u in bb],method='highs')
                if not res.success:
                    item[mode]=dict(success=False,message=res.message);continue
                # Use exact rational multipliers as a weak-duality certificate; the
                # floating solver is only a discovery method. Box endpoints are exact.
                lb=dual_lower(coef,eq,rhs,ine,irhs,bb,[q(v) for v in res.eqlin.marginals],
                              [min(F(0),q(v)) for v in res.ineqlin.marginals])
                assert lb<=base_value
                xs=res.x.reshape(24,5)
                err=max(np.max(abs(ae@res.x-np.asarray(rhs,dtype=float))),
                        np.max(ai@res.x-np.asarray(irhs,dtype=float)),
                        np.max(np.array([float(l) for l,u in bb])-res.x),
                        np.max(res.x-np.array([float(u) for l,u in bb])),
                        np.max(np.minimum(xs[:,1],xs[:,2])))
                item[mode]=dict(success=True,gap=float(base_value-lb),
                    gap_exact=[(base_value-lb).numerator,(base_value-lb).denominator],
                    candidate_saving=float(base_value)-res.fun,numerical_feasible=bool(err<=1e-6),
                    max_residual=float(err),terminal=float(xs[-1,-1]))
            results.append(item)
    stats={}
    for name in ('primary','alternative'):
        rows=[r for r in results if r['panel']==name]
        stats[name]={'n':len(rows),'service_exact_zero':sum(r['service_exact_zero'] for r in rows),
                     'service_mean_ceiling_MWh':float(np.mean([r['service_gap'] for r in rows])),
                     'service_max_ceiling_MWh':max(r['service_gap'] for r in rows),
                     'baseline_mean_shed_MWh':float(np.mean([r['baseline_shed'] for r in rows]))}
        for mode in ('same_stock','min_stock'):
            ok=[r[mode] for r in rows if r[mode]['success']]
            stats[name][mode]={'successful_LP':len(ok),
                'mean_certified_cost_ceiling_USD':float(np.mean([r['gap'] for r in ok])),
                'max_certified_cost_ceiling_USD':max(r['gap'] for r in ok),
                'numeric_feasible':sum(r['numerical_feasible'] for r in ok),
                'max_numeric_residual':max(r['max_residual'] for r in ok),
                'mean_numeric_candidate_saving_USD':float(np.mean([r['candidate_saving'] for r in ok]))}
    return {'manifest_entries_verified':integrity,
            'scope':'Retrospective synthetic case-model diagnostic; no online policy or site economics established.',
            'assumptions':{'energy_USD_per_MWh':50,'throughput_USD_per_MWh':10,'terminal_credit_USD_per_MWh':50,
                           'hourly_shed_fixed_to_exact_fill':'both arms','same_stock':'fixed to exact fill terminal inventory',
                           'min_stock':'original terminal floor and inventory credit; not identical terminal service',
                           'simultaneous_operation':'relaxed for the lower bound; checked numerically in candidates'},
            'summary':stats,'cases':results}
if __name__=='__main__':
    if len(sys.argv)!=3:raise SystemExit(__doc__)
    data=review(sys.argv[1])
    Path(sys.argv[2]).write_text(json.dumps(data,indent=2)+'\n')
    print(json.dumps(data['summary'],indent=2))
