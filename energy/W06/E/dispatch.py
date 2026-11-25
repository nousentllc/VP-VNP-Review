"""Causal controllers and exact full-information dynamic programming for the finite plant."""
import time
import numpy as np
from plant import BASIC, DGRID, HERE, INF, NEXT, NEXT_SOC, PREV, Q, SOC, START, back_step, stage, terminal, terminal_guard


def offline(rows,fixed=None,credit=50,tariff="variable",trade=False,certificate=True):
    clock=time.perf_counter_ns()
    v=terminal(fixed,credit)
    values=[v.tolist()] if certificate else []
    for row in reversed(rows):
        v=back_step(stage(row,tariff,trade)[0],v)
        if certificate: values.append(v.tolist())
    value=int(v[START])
    assert -INF<value<INF
    return dict(cents=value,fixed=fixed,credit=credit,tariff=tariff,trade=trade,
                potentials=values[::-1],elapsed_ns=time.perf_counter_ns()-clock)


def rule(row,state,ref,method,reachable,tariff="variable"):
    costs=stage(row,tariff)[0][state]
    valid=(costs<INF) & reachable[NEXT[state]]
    ids=np.flatnonzero(valid)
    if not len(ids):raise ValueError("No robustly feasible first action")
    if method=="fill":
        demand=row[1]+7*row[2]+4*row[3]
        desired=min(2,(40-demand)//11) if demand<=40 else -min(2,(demand-40+8)//9)
        return int(min(ids,key=lambda i:(abs(Q[i]-desired),abs(Q[i]),i)))
    marks=costs-Q*ref*100
    return int(min(ids,key=lambda i:(marks[i],abs(Q[i]),i)))


def rolling(issue,state,credit,remaining,guard,used):
    h=min(used,len(issue));last=len(guard)-1-remaining+h
    v=terminal(9,50) if remaining==h else terminal(None,credit)
    v=np.where(guard[last],v,INF)
    for k in reversed(range(h)):
        cost=stage(issue[k])[0]
        candidate=np.where((cost<INF)&(v[NEXT]<INF),cost+v[NEXT],INF)
        v=candidate.min(axis=1)
        if k==0:
            if v[state]>=INF:return None
            return int(np.argmin(candidate[state]))


def simulate(panel,method,ref,credit=0,terminal_match=True,tariff="variable",measure=True):
    start=time.perf_counter_ns()
    n=len(panel["actual"])
    guard=terminal_guard(n) if terminal_match else [np.ones_like(SOC,dtype=bool)]*(n+1)
    s=START; actions=[]; total=0
    for t,issue in enumerate(panel["issued_H12"]):
        tic=time.perf_counter_ns()
        row=issue[0];cost,bids,skips=stage(row,tariff)
        safe=rule(row,s,ref,"price",guard[t+1],tariff)
        fail=None
        if method in ("fill","price"):
            action=safe if method=="price" else rule(row,s,ref,"fill",guard[t+1],tariff)
        else:
            action=rolling(issue,s,credit,n-t,guard,6 if method=="h6" else 12)
            if action is None:
                fail="forecast_infeasible";action=safe
        if cost[s,action]>=INF or not guard[t+1][NEXT[s,action]]:
            fail="invalid";action=safe
        if (time.perf_counter_ns()-tic)>10**9:
            action=safe;fail="deadline"
        step=int(cost[s,action]);after=int(NEXT[s,action]);total+=step
        dt=time.perf_counter_ns()-tic
        actions.append([int(Q[action]),int(SOC[after]),int(bids[s,action] and tariff!="flat"),step,dt,fail])
        s=after
    if terminal_match: assert SOC[s]==9
    total-=int(SOC[s])*5000
    return dict(method=method,ref=ref,credit=credit,tariff=tariff,match_terminal=terminal_match,
                cents=total,final_soc=int(SOC[s]),actions=actions,wall_ns=time.perf_counter_ns()-start)


def stock_diagnostics(rows,fill_end):
    specs=[
        ("market_match9",9,50,"variable",False),
        ("market_matchfill",fill_end,50,"variable",False),
        ("market_floor0",None,0,"variable",False),
        ("market_floor50",None,50,"variable",False),
        ("market_floor100",None,100,"variable",False),
        ("flat_matchfill",fill_end,50,"flat",False),
        ("flat_floor50",None,50,"flat",False),
        ("optional_jobs",9,50,"variable",True),
    ]
    return {name:offline(rows,fixed,credit,tariff,allow_drop)
            for name,fixed,credit,tariff,allow_drop in specs}
