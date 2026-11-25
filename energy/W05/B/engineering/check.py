"""Independent exact post-run witness verifier and reporting tables. No optimizer is invoked."""
import argparse,csv,gzip,json,statistics
from collections import Counter
from fractions import Fraction as Q
from pathlib import Path
import numpy as np

def arr(v):return np.array(v,dtype=object) if not v else np.vectorize(Q,otypes=[object])(np.array(v,dtype=object))
def dump(path,rows):
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,list(rows[0]));w.writeheader();w.writerows(rows)
def evaluate(lp,c,A,b,E,d,cap):
    if lp['code']!=0:return False
    x,mu,nu=[arr(lp[k]) for k in ('x','mu','nu')]
    assert all(mu<=0) and all(A@x<=b) and all(E@x==d) and all(x>=0) and all(x<=cap)
    residual=c-A.T@mu-E.T@nu
    lower=b@mu+d@nu+sum(min(0,v)*u for v,u in zip(residual,cap))
    assert lower==Q(lp['L']) and c@x==Q(lp['U']) and c@x>=lower
    return True
def summary(primary,retries,destination):
    main=list(map(json.loads,gzip.open(primary,'rt')))
    retry=list(map(json.loads,gzip.open(retries,'rt')))
    assert len(main)==32 and len({(q['seed'],q['regime']) for q in main})==32
    rows=[];slots=[];fail=[];stats=Counter()
    def track(rec,panel):
        z=rec['model'];A,b,E,d,c,u,x0,S,G=[arr(z[k]) for k in ['A','b','E','d','c','cap','x0','S','G']]
        m=len(c);assert all(A@x0<=b) and all(E@x0==d)
        H=S@G-np.eye(m,dtype=int)
        assert np.all(E@H==0) and np.all(G@S==np.eye(len(G),dtype=int))
        h=np.array([sum(max(0,v)*q for v,q in zip(row,u)) for row in A@H])
        alpha=sum(max(0,v)*q for v,q in zip(c@H,u))
        assert np.all(h==arr(rec['h'])) and alpha==Q(rec['alpha'])
        assert evaluate(rec['full'],c,A,b,E,d,u) and evaluate(rec['reduced'],c@S,A@S,b+h,E@S,d,G@u)
        x=arr(rec['raw']);v=arr(rec['mix']);lam=Q(rec['lambda_min']);K=c@x;U=c@v
        sl=b-A@x0;vi=np.maximum(0,A@x-b)
        exact=max(dv/(dv+ds) if dv else 0 for dv,ds in zip(vi,sl))
        assert lam==exact and all(v==(1-lam)*x+lam*x0) and all(A@v<=b) and all(E@v==d)
        if lam>0:assert any(A@((1-lam/2)*x+lam/2*x0)>b)
        L=Q(rec['full']['L']);fu=Q(rec['full']['U']);lr=Q(rec['reduced']['L']);eps=K-lr
        beta=max(0,U-K);ub=Q(rec['uniform_beta']);lip=Q(rec['lipschitz_beta'])
        assert beta==Q(rec['beta']) and U-K==lam*(c@x0-K) and beta<=ub and beta<=lip
        assert U-(lr-alpha)<=alpha+beta+eps and U-max(L,lr-alpha)<=min(U-L,alpha+beta+eps)
        repair=rec['movement_matched_lp'];rdelta=None
        if repair['code']==0:
            y=arr(repair['x'])[:m]
            assert all(A@y<=b) and all(E@y==d) and all(y>=0) and all(y<=u)
            assert sum(abs(y-x))<=sum(abs(v-x)) and c@y==Q(repair['U']) and c@y<=U
            rdelta=U-c@y
        threshold=Q(1,1000)*max(1,abs(fu))
        row=dict(panel=panel,seed=rec['seed'],regime=rec['regime'],lambda_min=float(lam),violations=int(sum(vi>0)),alpha=float(alpha),
          beta=float(beta),uniform_beta=float(ub),lipschitz_beta=float(lip),reduced_eps=float(eps),bound=float(alpha+beta+eps),
          full_value=float(fu),regret_lower=float(max(0,U-fu)),regret_upper=float(U-L),exact_full=(fu==L),exact_reduced=(eps==0),
          candidate_bound_at_target=alpha+beta+eps<=threshold,uniform_bound_at_target=alpha+ub+eps<=threshold,
          direct_gap_at_target=U-L<=threshold,excess_over_movement_LP=None if rdelta is None else float(rdelta),
          anchor_build_ms=1000*rec['seconds']['anchor'],distortion_build_ms=1000*rec['seconds']['construct_projection'],
          analytic_repair_ms=1000*rec['seconds']['anchor_repair_validate'],movement_LP_ms=1000*rec['seconds']['movement_matched_repair_lp'],
          full_lp_ms=1000*rec['seconds']['full_reference_lp'])
        rows.append(row);stats[panel+'_one_sided_corruptions_rejected']+=int(lam>0)
        keep=[i for i,name in enumerate(z['labels']) if not name.startswith('terminal_')]
        a,q=A[keep],b[keep];e=arr(z['energy'])[:,-1,:];t=int(z['T'])
        for test in rec['terminal_controls']:
            dx=Q(test['terminal_change']);target=e@x0;target[0]+=dx
            valid=[]
            for j in range(t):
                delta=dx/e[0,j]
                # Directional headroom over ALL plant rows. This is independent of the candidate builder.
                if all(a[:,j]*delta<=q-a@x0) and 0<=x0[j]+delta<=u[j]:valid.append(j)
            assert valid==test['feasible_slots']
            lp=test['lp'];ok=lp['code']==0
            if ok:
                y=arr(lp['x'])[:m];assert all(a@y<=q) and all(e@y==target) and all(y>=0) and all(y<=u)
            if valid:
                w=arr(test['chosen'][1]);j=test['chosen'][2]
                assert j in valid and all(a@w<=q) and all(e@w==target) and sum(w!=x0)==1
            slots.append(dict(panel=panel,seed=rec['seed'],regime=rec['regime'],change=float(dx),valid_slots=len(valid),lp_feasible=ok,
                              lp_code=lp['code'],single_ms=1000*test['single_slot_s'],lp_ms=1000*test['fixed_mode_lp_s']))
    for rec in main:
        if 'failed' in rec:fail.append(dict(seed=rec['seed'],regime=rec['regime'],reason=rec['failed']))
        else:track(rec,'primary')
    for item in retry:
        z=item['original_model'];A,b,x0=[arr(z[k]) for k in ['A','b','x0']]
        assert max(A@x0-b)>0
        if 'retry' in item:track(item['retry'],'secondary')
    destination.mkdir(parents=True,exist_ok=True)
    dump(destination/'certificates.csv',rows);dump(destination/'slots.csv',slots);dump(destination/'primary_failures.csv',fail)
    summary={'scheduled':len(main),'primary_anchor_failures':len(fail),'secondary_attempts':len(retry),
      'secondary_lp_codes':dict(Counter(x['replacement_lp']['code'] for x in retry)),'mutations':dict(stats)}
    for panel in ['primary','secondary']:
        rr=[r for r in rows if r['panel']==panel];ss=[r for r in slots if r['panel']==panel]
        if not rr:continue
        summary[panel]=dict(accepted=len(rr),full_optimum_exact=sum(x['exact_full'] for x in rr),reduced_optimum_exact=sum(x['exact_reduced'] for x in rr),
                fallback_anchor=sum(x['lambda_min']==1 for x in rr),no_repair_needed=sum(x['lambda_min']==0 for x in rr),
                within_candidate_bound=sum(x['candidate_bound_at_target'] for x in rr),within_uniform_bound=sum(x['uniform_bound_at_target'] for x in rr),
                within_direct_gap=sum(x['direct_gap_at_target'] for x in rr),movement_lp_strict=sum((x['excess_over_movement_LP'] or 0)>1e-9 for x in rr),
                medians={k:statistics.median(x[k] for x in rr) for k in ['alpha','beta','uniform_beta','bound','regret_upper','lipschitz_beta','anchor_build_ms','distortion_build_ms','analytic_repair_ms','movement_LP_ms','full_lp_ms']},
                slots_total=len(ss),slots_certified=sum(bool(x['valid_slots']) for x in ss),slots_lp_only=sum(not x['valid_slots'] and x['lp_feasible'] for x in ss),
                slots_neither=sum(not x['valid_slots'] and not x['lp_feasible'] for x in ss))
    (destination/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
if __name__=='__main__':
    p=argparse.ArgumentParser()
    for k in ['primary','retries','output']:p.add_argument(k,type=Path)
    q=p.parse_args();summary(q.primary,q.retries,q.output)
