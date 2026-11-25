"""Post hoc reserve activation with robust finite-horizon one-call recovery and fixed adapted controllers."""
import argparse
import hashlib
import json
import sys
import time
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from plant import HERE, INF, SOC, PREV, Q, NEXT, WEAR, DGRID, SEEDS, START, back_step, terminal, read, save

BASE=Path(__file__).resolve().parent


def physical(act,power,locked,dem):
    end=SOC[:,None]+act
    valid=(np.abs(act)<=power)&(np.abs(act-PREV[:,None])<=2)&(end>=2)&(end<=11)&((act>=0)|(end>=locked))
    dgrid=np.maximum(act,0)*11+np.minimum(act,0)*9
    return valid&(dem+dgrid>=0)&(dem+dgrid<=90)


def end_state(act):
    soc=np.clip(SOC[:,None]+act,2,11)
    return (soc-2)*5+np.clip(act,-2,2)+2


def kernels(n):
    k0=np.zeros((n+1,50),dtype=bool);k1=k0.copy();k0[-1]=SOC==9;k1[-1]=SOC==9
    feasible={};offers={}
    for t in range(n-1,-1,-1):
        possible=[2] if t>=n-16 else [0,1,2]
        g0=[];g1=[]
        for powr in possible:
            up=min(powr,int(16<=t%24<22));dn=min(powr,int(t%24<6));locked=2 if powr==2 else 5
            def phys(a):
                # All bookings and protected demand lie in the interval [18,48] deci-MWh.
                return physical(a,powr,locked,18)&physical(a,powr,locked,48)
            nominal=phys(Q)&(Q>=-powr+up)&(Q<=powr-dn)
            g0.append((nominal&k0[t+1,NEXT]).any(axis=1))
            good=nominal&k1[t+1,NEXT]
            if up:good &= phys(Q-up)&k0[t+1,end_state(Q-up)]
            if dn:good &= phys(Q+dn)&k0[t+1,end_state(Q+dn)]
            possible_bid=(powr>0)&phys(Q-up-1)&k0[t+1,end_state(Q-up-1)]
            feasible[t,powr]=good;offers[t,powr]=possible_bid&good
            g1.append(good.any(axis=1))
        k0[t]=np.logical_and.reduce(g0);k1[t]=np.logical_and.reduce(g1)
    return k0,k1,feasible,offers


def costs(row,t,k):
    _,_,good,offer=k
    price,protected,hi,low,power,lock,up,dn,fee=row
    nominal=(protected+7*hi+4*low+DGRID)*price*10+WEAR
    return np.where(good[t,power],nominal-offer[t,power]*fee*100,INF)


def gate(p,k):
    clock=time.perf_counter_ns();v=terminal(9,50);records=[v.tolist()]
    for t in range(len(p["actual"])-1,-1,-1):
        v=back_step(costs(p["actual"][t],t,k),v);records.append(v.tolist())
    return dict(cents=int(v[START]),feasible=bool(v[START]<INF),potentials=records[::-1],wall_ns=time.perf_counter_ns()-clock)


def policy(p,k,arm):
    tic=time.perf_counter_ns();state=START;total=0;n=24*p["days"];acts=[]
    for t,issue in enumerate(p["issued_H12"]):
        clock=time.perf_counter_ns()
        m=costs(issue[0],t,k);admissible=k[2][t,issue[0][4]][state]
        choices=np.flatnonzero(admissible);fallback=None
        if not len(choices):return dict(failure_hour=t)
        safe=int(min(choices,key=lambda i:(m[state,i]-Q[i]*7000,abs(Q[i]),i)))
        a=safe
        if arm!="price":
            h=len(issue);loss=np.zeros(5,dtype=np.int64);allowed=admissible.copy()
            for err in ((-20,0,20) if arm=="scenario" else (0,)):
                v=terminal(9,50) if t+h==n else terminal(None,65)
                for lead in reversed(range(1,h)):
                    act=issue[lead].copy();act[0]=max(3,act[0]+int(err*min(1,lead/4)))
                    v=back_step(costs(act,t+lead,k),v)
                allowed &= v[NEXT[state]]<INF
                loss+=m[state]+v[NEXT[state]]
            if any(allowed):a=int(np.argmin(np.where(allowed,loss,10*INF)))
            else:fallback="planning_infeasible"
        if not admissible[a]:a=safe;fallback="unsafe"
        if time.perf_counter_ns()-clock>=10**9:a=safe;fallback="deadline"
        step=int(m[state,a]);total+=step
        bid=int(k[3][t,issue[0][4]][state,a]);state=int(NEXT[state,a])
        acts.append([int(Q[a]),int(SOC[state]),bid,step,time.perf_counter_ns()-clock,fallback])
    assert SOC[state]==9
    return dict(cents=total-45000,actions=acts,wall_ns=time.perf_counter_ns()-tic)


def run(out):
    start=time.perf_counter_ns()
    kby={};frozen={};gates=[];paths={}
    for days in (7,30):
        k=kernels(24*days);kby[days]=k
        save(out/f"kernels_{days}.json.gz",{"recovery":k[0].astype(int).tolist(),"standby":k[1].astype(int).tolist()})
        for seed in SEEDS:
            tag=f"{seed}_{days}";src=HERE/"inputs"/f"{tag}.json.gz";paths[tag]=read(src)
            frozen[tag]=hashlib.sha256(src.read_bytes()).hexdigest()
            rec=gate(paths[tag],k);save(out/f"certificate_{tag}.json.gz",rec)
            gates.append(dict(seed=seed,days=days,feasible=bool(k[1][0,START] and rec["feasible"]),offline_cents=rec["cents"],wall_ns=rec["wall_ns"]))
    save(out/"gates.json",dict(cases=gates,inputs_sha256=frozen,gate_complete_before_holdout_policy_costing=True))
    for row in gates:
        if not row["feasible"]:continue
        seed,days=row["seed"],row["days"];tag=f"{seed}_{days}"
        plans={arm:policy(paths[tag],kby[days],arm) for arm in ("price","continuation","scenario")}
        save(out/f"online_{tag}.json.gz",plans)
    save(out/"execution.json",{"total_ns":time.perf_counter_ns()-start})
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--out",type=Path,default=BASE/"results");run(p.parse_args().out)
