"""Predeclared post-primary challenge and explicit time-expanded network LP replication."""
import argparse
import time
from pathlib import Path

import numpy as np
from scipy.optimize import linprog
from scipy.sparse import coo_matrix

from audit import arc,STATES,trajectory
from dispatch import rule,simulate
from plant import HERE,INF,NEXT,SOC,Q,START,SEEDS,save,read,stage,terminal,terminal_guard,back_step


def scenario_policy(p,ref,tail):
    clock=time.perf_counter_ns();s=START;n=len(p["actual"]);guard=terminal_guard(n);actions=[];total=0
    for t,issue in enumerate(p["issued_H12"]):
        tic=time.perf_counter_ns()
        row=issue[0];cost,bid,_=stage(row);h=len(issue)
        safe=rule(row,s,ref,"price",guard[t+1]);loss=np.zeros(5,dtype=np.int64)
        alive=np.ones(5,dtype=bool)
        for err in (-20,0,20):
            v=terminal(9,50) if h==n-t else terminal(None,tail)
            v=np.where(guard[t+h],v,INF)
            for k in range(h-1,0,-1):
                f=issue[k].copy();f[0]=max(3,f[0]+int(err*min(1,k/4)))
                v=back_step(stage(f)[0],v)
            alive &= (cost[s]<INF)&(v[NEXT[s]]<INF)
            loss+=cost[s]+v[NEXT[s]]
        fail=None
        if not any(alive):a=safe;fail="forecast_infeasible"
        else:a=int(np.argmin(np.where(alive,loss,10*INF)))
        if cost[s,a]>=INF or not guard[t+1][NEXT[s,a]]:a=safe;fail="invalid"
        if time.perf_counter_ns()-tic>10**9:a=safe;fail="deadline"
        total+=int(cost[s,a]);actions.append([int(Q[a]),int(SOC[NEXT[s,a]]),int(bid[s,a]),int(cost[s,a]),time.perf_counter_ns()-tic,fail])
        s=int(NEXT[s,a])
    assert SOC[s]==9
    return dict(method="scenario",ref=ref,credit=tail,tariff="variable",match_terminal=True,cents=total-45000,
                final_soc=9,actions=actions,wall_ns=time.perf_counter_ns()-clock)


def flow_lp(issue,state,selected):
    clock=time.perf_counter_ns();h=len(issue)
    # Pure state-action network flow. Terminal arcs to a free sink, no continuation in this first-day check.
    head=[];tail=[];obj=[]
    for k,r in enumerate(issue):
        for i,(s,p) in enumerate(STATES):
            for q in range(-2,3):
                x=arc(r,s,p,q)
                if x is None:continue
                head.append((k+1)*50+x[0]);tail.append(k*50+i);obj.append(x[1])
    for i in range(50):head.append((h+1)*50);tail.append(h*50+i);obj.append(0)
    m=len(obj);head=np.asarray(head);tail=np.asarray(tail)
    a=coo_matrix((np.r_[np.ones(m),-np.ones(m)],(np.r_[tail,head],np.tile(np.arange(m),2))),shape=((h+1)*50+1,m)).tocsr()
    b=np.zeros((h+1)*50+1);b[state]=1;b[-1]=-1
    res=linprog(obj,A_eq=a,b_eq=b,bounds=(0,None),method="highs")
    assert res.success,res.message
    v=np.zeros(50,dtype=np.int64)
    for k in range(h-1,0,-1):v=back_step(stage(issue[k])[0],v)
    first=stage(issue[0])[0][state]+v[NEXT[state]]
    exact=int(min(first));assert abs(res.fun-exact)<1e-6 and first[selected+2]==exact
    return dict(lp_cents=float(res.fun),dp_cents=exact,selected=selected,columns=m,
                rows=a.shape[0],seconds=(time.perf_counter_ns()-clock)/1e9,lp_status=res.message)


def run(out):
    initial=time.perf_counter_ns();rdir=out/"results";ref=read(rdir/"gate.json")["ref"];credit=read(rdir/"continuation_fit.json")["selected"]
    rows=[];checks=[]
    for seed in SEEDS:
        for d in (7,30):
            tag=f"{seed}_{d}";p=read(out/"inputs"/f"{tag}.json.gz");primary=read(rdir/f"online_{tag}.json.gz")
            controls={"mark50":simulate(p,"mark50",ref,50),"scenario":scenario_policy(p,ref,credit)}
            if seed==SEEDS[0] and d==7:
                st=START
                for t in range(24):
                    a=primary["h12"]["actions"][t];checks.append(flow_lp(p["issued_H12"][t],st,a[0]))
                    st=int(NEXT[st,a[0]+2])
            details={k:trajectory(p["actual"],v) for k,v in controls.items()}
            rows.append(dict(seed=seed,days=d,
                candidate_saving_vs_control_USD_per_day={k:(v["cents"]-primary["continuation"]["cents"])/100/d for k,v in controls.items()},
                details=details))
            save(rdir/f"supplement_{tag}.json.gz",controls)
    save(rdir/"supplement_summary.json",dict(cases=rows,lp_checks=checks,wall_ns=time.perf_counter_ns()-initial))
    for d in (7,30):
        print(d,{k:float(np.mean([c["candidate_saving_vs_control_USD_per_day"][k] for c in rows if c["days"]==d])) for k in controls})
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--out",type=Path,default=HERE);run(p.parse_args().out)
