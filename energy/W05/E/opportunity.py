"""Post-freeze paired feasible upper and unrestricted clairvoyant LP lower certificates."""
import argparse,csv,gzip,json,hashlib
from fractions import Fraction as Q
from pathlib import Path
from policies import ROOT,W04,read,dump,P,old,np
from scipy.optimize import linprog
from scipy.sparse import vstack,csr_matrix
from audit import write

def rational(value):
    return Q(float(value))
def record(x):
    return [x.numerator,x.denominator]

def exact_schedule(c):
    cap=rational(P['grid_cap']);E=rational(P['energy']);power=rational(P['power']);r=rational(P['ramp'])
    eta=rational(P['eta_c']);draw=rational(1./P['eta_d'])
    state=rational(P['initial']);prev=rational(P['previous'])
    plan=[]
    for t in range(24):
        load=rational(c['load'][t]);floor=rational(c['floor'][t]);avail=bool(c['available'][t])
        hi=min(cap,prev+r);p=power*avail
        ds=min(max(0,p-rational(c['reserve'][t])),max(0,load-hi),max(0,state-floor)/draw)
        ch=0 if ds>0 else min(p,(E-state)/eta,max(max(0,(floor-state)/eta),min(max(0,hi-load),(E-state)/eta)))
        g=min(hi,load+ch-ds);u=load-g+ch-ds;after=state+eta*ch-draw*ds
        if not (0<=g<=cap and abs(g-prev)<=r and 0<=ch<=p and 0<=ds<=max(0,p-rational(c['reserve'][t]))
                and ch*ds==0 and 0<=u<=load-rational(P['facility']) and floor<=after<=E
                and g+ds-ch+u==load):
            raise ValueError(c['id'])
        plan.append([Q(x) for x in (g,ch,ds,u,after)])
        state,prev=after,g
    return plan

def check(c,raw):
    net=old.matrix(c['load'],c['available'],c['floor'],c['reserve'],P['initial'],P['previous'])
    ids,eq,b,ineq,d,box=net
    cost=np.zeros(120);cost[ids[:,3]]=1
    out=linprog(cost,A_eq=eq,b_eq=b,A_ub=ineq,b_ub=d,bounds=box,method='highs-ds',options=old.OPTIONS)
    if not out.success:raise RuntimeError(out.message)
    y=list(map(rational,out.eqlin.marginals));z=[min(Q(0),rational(t)) for t in out.ineqlin.marginals]
    discounts=y+z;rhs=list(map(rational,b+d))
    At=vstack([csr_matrix(eq),csr_matrix(ineq)]).tocsc()
    residual=list(map(rational,cost))
    lower=sum(x*v for x,v in zip(discounts,rhs))
    for j,(l,u) in enumerate(box):
        for k in range(At.indptr[j],At.indptr[j+1]):residual[j]-=discounts[At.indices[k]]*rational(At.data[k])
        lower+=residual[j]*rational(l if residual[j]>=0 else u)
    plan=exact_schedule(c);x=[v for h in plan for v in h]
    # Audit against literal stored matrix apart from the independently reconstructed engineering equations.
    M=At.tocsr()
    for i,limit in enumerate(rhs):
        val=sum(rational(M.data[j])*x[M.indices[j]] for j in range(M.indptr[i],M.indptr[i+1]))
        if (i<len(y) and val!=limit) or val>limit:raise ValueError((c['id'],i,'constraint'))
    assert all(rational(l)<=x[j]<=rational(u) for j,(l,u) in enumerate(box))
    upper=sum(h[3] for h in plan);gap=upper-lower
    if gap<0:raise ValueError('Inverted exact bounds')
    delta=float(np.max(abs(np.array(plan,dtype=float)-np.asarray(raw['actions']))))
    summary=dict(case=c['id'],seed=c['seed'],panel=c['panel'],regime=c['regime'],exact_U=float(upper),exact_L=float(lower),
        certified_upper_on_improvement_MWh=float(gap),exact_zero=bool(gap==0),below_0p1_MWh=bool(gap<Q(1,10)),max_nominal_vs_live_action=delta)
    cert=dict(case=c['id'],upper=record(upper),lower=record(lower),gap=record(gap),eq_multipliers=[record(q) for q in y],
              le_multipliers=[record(q) for q in z],primal=[[record(v) for v in hour] for hour in plan])
    return summary,cert

def run(primary,out):
    output=Path(out);output.mkdir(parents=True,exist_ok=True);cases=read(ROOT/'inputs/holdout.json.gz')['cases']
    with gzip.open(primary,'rt') as f:raw={r['case']:r for r in (json.loads(s) for s in f) if r['arm']=='rule12'}
    rows=[];proofs=[]
    for c in cases:
        s,p=check(c,raw[c['id']]);rows.append(s);proofs.append(p)
    write(output/'opportunity.csv',rows);dump(output/'opportunity_certificates.json.gz',proofs)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--primary',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();run(a.primary,a.out)
