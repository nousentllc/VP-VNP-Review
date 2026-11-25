"""Constructive projection/lift audit. Run on W05 frozen case IDs only after locking."""
import argparse, datetime, gzip, hashlib, json, os, sys, time
from fractions import Fraction as F
from pathlib import Path
for var in ('OPENBLAS_NUM_THREADS','VECLIB_MAXIMUM_THREADS','MKL_NUM_THREADS','OMP_NUM_THREADS'):os.environ[var]='1'
import numpy as np
from model import fleet,zeros
from exact_lp import solve,support
HERE=Path(__file__).resolve().parent
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def encode(z):
    if isinstance(z,np.ndarray):return encode(z.tolist())
    if isinstance(z,(list,tuple)):return [encode(v) for v in z]
    if isinstance(z,dict):return {k:encode(v) for k,v in z.items()}
    if isinstance(z,F):return str(z)
    if isinstance(z,np.generic):return z.item()
    return z

def l1_repair(c,A,b,E,d,cap,ref,radius=None):
    n=len(cap);I=zeros((n,n));np.fill_diagonal(I,F(1));blank=zeros((len(b),n))
    a=np.vstack((np.c_[A,blank],np.c_[I,-I],np.c_[-I,-I]))
    rhs=np.r_[b,ref,-ref];box=np.r_[cap,[max(u,abs(q),abs(u-q)) for q,u in zip(ref,cap)]]
    if radius is None:
        objective=np.r_[zeros(n),[F(1)]*n]
    else:
        a=np.vstack((a,np.r_[zeros(n),[F(1)]*n]));rhs=np.r_[rhs,radius];objective=np.r_[c,zeros(n)]
    lp=solve(objective,a,rhs,np.c_[E,zeros((len(d),n))],d,box)
    return lp

def one(seed,regime):
    clock=time.perf_counter;start=clock()
    z=fleet(seed,regime);A,b,E,d,c,u,x0,S,G=[z[k] for k in ['A','b','E','d','c','cap','x0','S','G']]
    anchor_time=clock()-start
    # Each coordinate of Gx is an average. If all device caps agree in the block,
    # the lifted block coordinate is covered by the SAME nameplate bound.
    k=len(G);n=len(c);P=S@G;I=zeros((n,n));np.fill_diagonal(I,F(1))
    assert np.all(E@(P-I)==0)
    assert np.all(S@(G@u)==u)
    h=np.array([support(v,u) for v in A@(P-I)],dtype=object)
    alpha=support(c@(P-I),u)
    theoretical_build=clock()-start-anchor_time
    stamp=clock();reduced=solve(c@S,A@S,b+h,E@S,d,G@u);reduced_s=clock()-stamp
    stamp=clock();full=solve(c,A,b,E,d,u);full_s=clock()-stamp
    row=dict(seed=seed,regime=regime,model=z,h=h,alpha=alpha,full=full,reduced=reduced,seconds=dict(anchor=anchor_time,
             construct_projection=theoretical_build,reduced_lp=reduced_s,full_reference_lp=full_s))
    if reduced['code'] or full['code']:return row
    stamp=clock();raw=S@reduced['x'];slack=b-A@x0;viol=np.maximum(F(0),A@raw-b)
    ratios=[q/(q+s) if q else F(0) for q,s in zip(viol,slack)]
    lam=max(ratios);mix=(1-lam)*raw+lam*x0
    worst=max(v/(v+s) if v else F(0) for v,s in zip(h,slack))
    assert all(A@mix<=b) and all(E@mix==d) and all(mix>=0) and all(mix<=u)
    J=c@mix;K=c@raw;aff=J-K; beta=max(F(0),aff)
    uniform_beta=worst*max(F(0),c@x0+support(-c,u))
    liploss=max(abs(c))*sum(abs(raw-x0))*lam
    eps=K-reduced['L'];true_regret_upper=J-full['L']
    assert aff==lam*(c@x0-K) and beta<=liploss and beta<=uniform_beta
    assert J-full['U']<=alpha+beta+eps and full['L']<=J
    # Cost over the set of feasible repairs within the anchor repair's L1 distance.
    row['seconds']['anchor_repair_validate']=clock()-stamp;stamp=clock()
    repair=l1_repair(c,A,b,E,d,u,raw,sum(abs(raw-mix)))
    row['seconds']['movement_matched_repair_lp']=clock()-stamp
    if repair['code']==0:assert repair['L']<=J and repair['U']<=J+F(1,1000000)
    row.update(raw=raw,mix=mix,lambda_min=lam,lambda_uniform=worst,alpha_beta_eps=alpha+beta+eps,beta=beta,uniform_beta=uniform_beta,
               lipschitz_beta=liploss,affine_change=aff,cost=J,raw_cost=K,full_regret_lower=max(F(0),J-full['U']),
               full_regret_upper=true_regret_upper,violated_rows=int(np.sum(viol>0)),limiting=[z['labels'][i] for i,r in enumerate(ratios) if r==lam and lam>0],
               movement_matched_lp=repair)
    # Separate intervention from the reduced LP. Impose a *new*, exact terminal SOC
    # for device 0 while retaining the anchor's terminal state for all other units.
    keep=[i for i,label in enumerate(z['labels']) if not label.startswith('terminal_')]
    a,q=A[keep],b[keep];end=z['energy'][:,-1,:];target0=end@x0
    tests=[]
    for change in [F(1),F(-1),F(7),F(-7)]:
        ts=clock();target=target0.copy();target[0]+=change;options=[];failures=[]
        for j in range(z['T']):
            v=x0.copy();v[j]+=change/end[0,j]
            err=max(max(a@v-q),max(v-u),max(-v),max(abs(end@v-target)))
            if err<=0:options.append((c@v,v,j))
            else:failures.append((j,err))
        t_sec=clock()-ts;chosen=min(options,key=lambda v:v[0]) if options else None
        ts=clock();lp=l1_repair(c,a,q,end,target,u,x0);elapsed=clock()-ts
        tests.append(dict(terminal_change=change,actual_target=target,feasible_slots=[v[2] for v in options],
                   chosen=chosen,failed_rows_max=failures,lp=lp,single_slot_s=t_sec,fixed_mode_lp_s=elapsed))
    row['terminal_controls']=tests
    return row

def main():
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['dev','freeze','run']);ap.add_argument('out',type=Path);args=ap.parse_args()
    paths=[HERE/n for n in ['model.py','campaign.py','exact_lp.py','plan.md']]
    if args.action=='freeze':
        if args.out.exists():raise ValueError('prospective lock already exists')
        entry=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),sha256={p.name:digest(p) for p in paths},
                   seeds=list(range(17031,17039)),regimes=['slack','tight','boundary','outage'],n=3,h=8)
        args.out.write_text(json.dumps(entry,indent=2)+'\n');return
    if args.action=='dev':panel=[(9003,'slack'),(9005,'boundary')]
    else:
        lock=json.loads((HERE/'freeze.json').read_text())
        assert all(digest(p)==lock['sha256'][p.name] for p in paths)
        panel=[(s,r) for s in lock['seeds'] for r in lock['regimes']]
    if args.out.exists():raise ValueError('choose a fresh output')
    with gzip.open(args.out,'xt') as f:
        for seed,regime in panel:
            t=time.perf_counter()
            try:r=one(seed,regime)
            except Exception as err:
                import traceback
                r=dict(seed=seed,regime=regime,failed=repr(err),trace=traceback.format_exc())
            r['elapsed']=time.perf_counter()-t;f.write(json.dumps(encode(r),separators=(',',':'))+'\n')
            print(seed,regime,r.get('failed','ok'),flush=True)
if __name__=='__main__':main()
