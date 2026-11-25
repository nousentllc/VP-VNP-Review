"""Post hoc tighter distortion certificates by original-polytope support LPs."""
import argparse,csv,gzip,json,time
from pathlib import Path
from fractions import Fraction as Q
import numpy as np
from campaign import encode
from check import arr,evaluate
from exact_lp import solve,support

def sparse(vec):return [[j,str(x)] for j,x in enumerate(vec) if x]
def expand(xs,n):
    a=np.full(n,Q(0),dtype=object)
    for j,v in xs:a[j]=Q(v)
    return a

def process(rec):
    t=time.perf_counter();z=rec['model']
    A,b,E,d,c,u,x0,S,G=[arr(z[k]) for k in ['A','b','E','d','c','cap','x0','S','G']]
    P=S@G-np.eye(len(c),dtype=int);cs=[c@P,*list(A@P)]
    bounds=[];duals=[];cache={};fallback=0
    for j,v in enumerate(cs):
        key=tuple(v)
        if key not in cache:
            original=support(v,u)
            if original==0:
                entry=dict(upper=Q(0),method='box',key=j)
            else:
                lp=solve(-v,A,b,E,d,u)
                if lp.get('code')!=0:
                    entry=dict(upper=original,method='box',key=j,failure=lp.get('status'));fallback+=1
                else:
                    entry=dict(upper=min(original,max(Q(0),-lp['L'])),method='dual',key=j,mu=sparse(lp['mu']),nu=sparse(lp['nu']))
            cache[key]=entry
            duals.append(entry)
        bounds.append(cache[key]['upper'])
    alpha=bounds[0];h=np.array(bounds[1:],dtype=object);pre=time.perf_counter()-t;t=time.perf_counter()
    lp=solve(c@S,A@S,b+h,E@S,d,G@u)
    if lp['code']!=0:return dict(seed=rec['seed'],regime=rec['regime'],failure=lp['status'],certificates=duals)
    x=S@lp['x'];sl=b-A@x0;vi=np.maximum(0,A@x-b)
    lam=max(q/(q+s) if q else Q(0) for q,s in zip(vi,sl));xp=(1-lam)*x+lam*x0
    assert all(A@xp<=b) and all(E@xp==d) and all(xp>=0) and all(xp<=u)
    U=c@xp;K=c@x;bound=alpha+max(0,U-K)+K-lp['L']
    assert U-(lp['L']-alpha)<=bound
    return dict(seed=rec['seed'],regime=rec['regime'],alpha=alpha,h=h,certificates=duals,lp=lp,mix=xp,lam=lam,
                fullgap=U-Q(rec['full']['L']),bound=bound,boxfallback=fallback,pre_s=pre,solve_repair_s=time.perf_counter()-t)

def run(primary,out,checkmode):
    base=[r for r in map(json.loads,gzip.open(primary,'rt')) if 'failed' not in r]
    if not checkmode:
        with gzip.open(out,'xt') as f:
            for row in base:
                result=process(row);f.write(json.dumps(encode(result),separators=(',',':'))+'\n')
        return
    checks=list(map(json.loads,gzip.open(out,'rt')));nproof=0;rows=[]
    assert len(checks)==len(base)
    for r,q in zip(base,checks):
        assert (r['seed'],r['regime'])==(q['seed'],q['regime'])
        z=r['model'];A,b,E,d,c,u,x0,S,G=[arr(z[k]) for k in ['A','b','E','d','c','cap','x0','S','G']]
        P=S@G-np.eye(len(c),dtype=int)
        cs=[c@P,*list(A@P)];limits={}
        for s in q['certificates']:
            v=cs[s['key']];vbox=support(v,u)
            if s['method']=='dual':
                mu=expand(s['mu'],len(b));nu=expand(s['nu'],len(d));assert all(mu<=0)
                weak=-(b@mu+d@nu)+support(v+A.T@mu+E.T@nu,u)
                expect=min(vbox,max(0,weak));nproof+=1
            else:expect=vbox
            assert Q(s['upper'])==expect;limits[tuple(v)]=expect
        if 'failure' in q:continue
        alpha=Q(q['alpha']);h=arr(q['h'])
        assert [limits[tuple(v)] for v in cs]==[alpha,*h]
        assert evaluate(q['lp'],c@S,A@S,b+h,E@S,d,G@u)
        x=arr(q['mix']);assert all(A@x<=b) and all(E@x==d)
        tol=Q(1,1000)*max(1,abs(Q(r['full']['U'])))
        rows.append(dict(seed=r['seed'],regime=r['regime'],box_alpha=float(Q(r['alpha'])),support_alpha=float(alpha),box_bound=float(Q(r['alpha_beta_eps'])),
                         support_bound=float(Q(q['bound'])),old_U=float(Q(r['cost'])),new_U=float(c@x),
                         support_lp_ms=1000*q['pre_s'],support_target=Q(q['bound'])<=tol,fullgap=float(Q(q['fullgap'])),
                         direct_ms=1000*r['seconds']['full_reference_lp']))
    dest=out.with_name('support_analysis.csv')
    with dest.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    print('audit',len(rows),nproof,'dual certificates')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('primary',type=Path);p.add_argument('output',type=Path);p.add_argument('--check',action='store_true')
    a=p.parse_args();run(a.primary,a.output,a.check)
