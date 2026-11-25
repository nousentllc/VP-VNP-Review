"""Independent integer plant and Bellman checker. Reads published paths, controller actions and potentials."""
import argparse
import csv
import gzip
import json
import math
import statistics as stat
import time
from pathlib import Path

import numpy as np

HERE=Path(__file__).resolve().parent
BIG=10**12
STATES=[(s,p) for s in range(2,12) for p in (-2,-1,0,1,2)]
INDEX={pair:k for k,pair in enumerate(STATES)}
SEEDS=[69103,69119,69143,69157,69179,69203,69221,69239]


def load(path):
    return json.loads(gzip.decompress(path.read_bytes()) if path.suffix==".gz" else path.read_bytes())


def arc(row,s,p,q,flat=False,can_skip=False):
    price,facility,nhi,nlow,power,locked,up,down,fee=row
    after=s+q
    if abs(q-p)>2 or after<2 or after>11 or q < up-power or q > power-down:
        return None
    if q<0 and after<locked:return None
    hi=nhi*7;lo=nlow*4
    delta=11*q if q>=0 else 9*q
    missed=nlow if can_skip and price>45 else 0
    grid=facility+hi+lo+delta-missed*4
    if grid<0 or grid>90:return None
    bid=int(not flat and power>0 and q-1>=up-power and after-1>=locked)
    imp=grid*(50 if flat else price)*10
    wear=abs(delta)*(100 if flat else 80)+(600 if not flat and abs(q)==2 else 0)
    reach=INDEX[(after,q)]
    return (reach,imp+wear-100*bid*fee+1800*missed,grid,wear,bid,missed,imp)


def all_arcs(row,flat,optional):
    # Sparse arc list from independent scalar engineering equations.
    edges=[]
    for i,(soc,prev) in enumerate(STATES):
        for q in (-2,-1,0,1,2):
            a=arc(row,soc,prev,q,flat,optional)
            if a is not None:edges.append((i,a[0],a[1],q,a[5]))
    return np.asarray(edges,dtype=np.int64).T


def cap(row):
    return int(row[0])


def forecast_check(p):
    n=len(p["actual"]); boundaries=[];hiarr=loarr=0
    for t,(row,issue) in enumerate(zip(p["actual"],p["issued_H12"],strict=True)):
        assert len(issue)==min(12,n-t) and row==issue[0] and len(row)==9
        assert row[2]==(p["arrivals"][t-2][0] if t>=2 else 0)
        assert row[3]==(p["arrivals"][t-5][1] if t>=5 else 0)
        hiarr+=p["arrivals"][t][0]-row[2];loarr+=p["arrivals"][t][1]-row[3]
        assert hiarr>=0 and loarr>=0
        if t%24==23 and t<n-1:boundaries.append([hiarr,loarr])
        def mean(h):
            a=h%24
            return 34 if a<6 else 69 if a<16 else 121 if a<22 else 52
        for k,f in enumerate(issue[1:],1):
            u=t+k;h=u%24
            hjob=p["arrivals"][u-2][0] if 0<=u-2<=t else int(u>=2)
            ljob=p["arrivals"][u-5][1] if 0<=u-5<=t else int(u>=5)
            power=row[4] if k==1 and u<n-16 else 2
            assert f==[max(3,round(mean(u)+.65**k*(row[0]-mean(t)))),20+4*(8<=h<20),
                       hjob,ljob,power,5 if power!=2 else 2,min(power,int(16<=h<22)),
                       min(power,int(h<6)),15 if 15<=h<22 else 4]
    assert hiarr==loarr==0
    return dict(midnights=len(boundaries),nonempty_midnights=sum(sum(v)>0 for v in boundaries),
                high_obligations_crossing=sum(v[0] for v in boundaries),low_obligations_crossing=sum(v[1] for v in boundaries))


def trajectory(actual,plan):
    soc=9;prev=0;total=imports=wear=bidfees=cost=charge=draw=high=low=protected=outage=0
    clocks=[];reasons={};states_at_midnight=[]
    for t,(row,action) in enumerate(zip(actual,plan["actions"],strict=True)):
        q,after,bid,step,dt,fail=action;z=arc(row,soc,prev,q)
        assert z is not None and STATES[z[0]]==(after,q) and z[1]==step and z[4]==bid and z[5]==0
        total+=step;imports+=z[2];wear+=z[3];bidfees+=100*bid*row[-1];cost+=z[6]
        high+=row[2];low+=row[3];protected+=row[1];outage+=row[4]==0
        charge+=max(q,0);draw+=max(-q,0);clocks.append(dt)
        if fail:reasons[fail]=reasons.get(fail,0)+1
        soc=after;prev=q
        if t%24==23 and t+1<len(actual):states_at_midnight.append([soc,prev])
    assert total-5000*soc==plan["cents"] and total==cost+wear-bidfees
    assert not plan["match_terminal"] or soc==9
    return dict(cents=plan["cents"],terminal_MWh=soc,import_MWh=imports/10,energy_cash_USD=cost/100,
                wear_USD=wear/100,reserve_receipts_USD=bidfees/100,loss_MWh=(charge+draw)/10,
                throughput_AC_MWh=(11*charge+9*draw)/10,high_jobs=high,low_jobs=low,
                protected_MWh=protected/10,unserved_protected_MWh=0,missed_low_jobs=0,missed_high_jobs=0,
                inventory_credit_USD=50*soc,outage_hours=outage,states_at_midnight=states_at_midnight,
                fallback_reasons=reasons,steps=len(clocks),max_step_ms=max(clocks)/1e6,
                p95_step_ms=float(np.quantile(clocks,.95))/1e6,wall_s=plan["wall_ns"]/1e9,
                timed_step_s=sum(clocks)/1e9,deadline_misses=sum(c>1_000_000_000 for c in clocks))


def check_offline(rows,cert,cache):
    v=np.asarray(cert["potentials"],dtype=np.int64);n=len(rows);f=cert["fixed"];cr=cert["credit"]
    assert v.shape==(n+1,50)
    assert list(v[-1])==[-cr*s*100 if f is None or s==f else BIG for s,p in STATES]
    state=INDEX[9,0];total=0;missed=0;bids=0;visited=0
    for t,row in enumerate(rows):
        key=tuple(row),cert["tariff"]=="flat",cert["trade"]
        if key not in cache:
            cache[key]=all_arcs(row,key[1],key[2])
        i,j,c,q,dropped=cache[key]
        sums=np.where(v[t+1,j]<BIG,c+v[t+1,j],BIG)
        # Lower Bellman inequalities for every feasible edge, equality for every finite state.
        best=np.full(50,BIG,dtype=np.int64);np.minimum.at(best,i,sums)
        assert np.array_equal(best,v[t]),(t,cert["fixed"],cert["credit"])
        k=np.flatnonzero((i==state)&(sums==v[t,state]))[0]
        assert sums[k]<BIG
        total+=int(c[k]);missed+=int(dropped[k]);state=int(j[k]);visited+=len(i)
    terminal=STATES[state][0]
    assert total-terminal*100*cr==cert["cents"]==v[0,INDEX[9,0]]
    return dict(cents=cert["cents"],terminal=terminal,missed_low_jobs=missed,checked_edges=visited)


def simple_flat(rows,end):
    # Starting stock 9 is feasible at every hour with zero action, fixed baseline or relaxed stock.
    # If end differs, require actual admissible monotone path before using this analytic optimum.
    diff=end-9
    reach={(9,0)}
    for row in rows:
        step=set()
        for s,prev in reach:
            for q in range(min(diff,0),max(diff,0)+1):
                if abs(q)>2 or (q>0 and s+q>end) or (q<0 and s+q<end):continue
                a=arc(row,s,prev,q,True,False)
                if a:step.add(STATES[a[0]])
        reach=step
    assert any(s==end for s,_ in reach)
    base=sum(r[1]+7*r[2]+4*r[3] for r in rows)*500-9*5000
    return base+max(0,diff)*1600+max(0,-diff)*1400,base


def verify(out):
    clock=time.perf_counter_ns();rec=[];summ=[];gate=load(out/"results/gate.json")
    for seed in SEEDS:
        for days in (7,30):
            caseclock=time.perf_counter_ns();tag=f"{seed}_{days}";p=load(out/"inputs"/f"{tag}.json.gz")
            pilot=load(out/"results"/f"baseline_{tag}.json.gz")
            controllers=load(out/"results"/f"online_{tag}.json.gz")
            controllers.update(price=pilot["price"],free_fill=pilot["free_fill"])
            c=load(out/"results"/f"cert_{tag}.json.gz")
            queues=forecast_check(p);cache={}
            results={name:check_offline(p["actual"],o,cache) for name,o in c.items()}
            stats={name:trajectory(p["actual"],a) for name,a in controllers.items()}
            for name,a in stats.items():
                if controllers[name]["match_terminal"]:assert a["cents"]>=results["market_match9"]["cents"]
            for k,row in enumerate(pilot["reset"]):
                assert (row["same"],row["loose"])==simple_flat(p["actual"][24*k:24*k+24],row["end"])
            assert (c["flat_matchfill"]["cents"],c["flat_floor50"]["cents"])==simple_flat(p["actual"],stats["free_fill"]["terminal_MWh"])
            assert stats["price"]["cents"]==next(r["price_cents"] for r in gate["cases"] if r["seed"]==seed and r["days"]==days)
            rec.append(dict(seed=seed,days=days,queue=queues,offline=results,online=stats,
                            reset_gap=sum(d["same"]-d["loose"] for d in pilot["reset"]),
                            audit_wall_s=(time.perf_counter_ns()-caseclock)/1e9))
    (out/"results/audit.json").write_text(json.dumps(rec,indent=2)+"\n")
    tests=[]
    for days in (7,30):
        st=[r for r in rec if r["days"]==days];n=len(st)
        def daily(fn):return [fn(r)/(days*100) for r in st]
        def summary(nums):return dict(mean=stat.mean(nums),min=min(nums),max=max(nums),median=stat.median(nums))
        table={arm:summary(daily(lambda r:r["online"][arm]["cents"]-r["offline"]["market_match9"]["cents"])) for arm in ("price","fill","h6","h12","continuation")}
        contrasts={}
        for ref in ("price","h12"):
            gain=daily(lambda r:r["online"][ref]["cents"]-r["online"]["continuation"]["cents"])
            wins=sum(x>15 for x in gain);pval=sum(math.comb(n,k) for k in range(wins,n+1))/2**n
            tests.append(dict(days=days,ref=ref,wins=wins,p=pval))
            contrasts[ref]=dict(**summary(gain),positive=sum(x>0 for x in gain),above_15=wins,values=gain)
        stats=dict(days=days,PF_headroom_USD_per_day=table,candidate_gain_USD_per_day=contrasts,
            exact_hourly_service_stock_effect_USD_per_day={
            "flat":summary(daily(lambda r:r["offline"]["flat_matchfill"]["cents"]-r["offline"]["flat_floor50"]["cents"])),
            "flat_artificial_daily_reset":summary(daily(lambda r:r["reset_gap"])),
            "market":summary(daily(lambda r:r["offline"]["market_matchfill"]["cents"]-r["offline"]["market_floor50"]["cents"]))},
            optional_job_tradeoff_mean_jobs_missed=stat.mean(r["offline"]["optional_jobs"]["missed_low_jobs"] for r in st),
            optional_job_tradeoff_max_available_benefit_USD_per_day=summary(daily(lambda r:r["offline"]["market_match9"]["cents"]-r["offline"]["optional_jobs"]["cents"])),
            cross_midnight_queues=sum(r["queue"]["nonempty_midnights"] for r in st),
            total_midnights=sum(r["queue"]["midnights"] for r in st),
            credits_to_compare_at_equal_base_service={},all_cert_checked_edges=sum(y["checked_edges"] for r in st for y in r["offline"].values()))
        for k in ("market_floor0","market_floor50","market_floor100"):
            stats["credits_to_compare_at_equal_base_service"][k]=[r["offline"][k]["terminal"] for r in st]
        summ.append(stats)
    alpha=.05;prev=0.
    for idx,r in enumerate(sorted(tests,key=lambda t:t["p"])):
        prev=max(prev,min(1,(len(tests)-idx)*r["p"]));r["holm_adjusted_p"]=prev;r["reject"]=prev<=alpha
    report=dict(panels=summ,tests=tests,clocks=dict(audit_wall_s=(time.perf_counter_ns()-clock)/1e9,
                decision_count=sum(x["steps"] for r in rec for x in r["online"].values()),
                total_reported_deadline_misses=sum(x["deadline_misses"] for r in rec for x in r["online"].values()),
                max_step_ms=max(x["max_step_ms"] for r in rec for x in r["online"].values()),
                fallback_events=sum(sum(x["fallback_reasons"].values()) for r in rec for x in r["online"].values())))
    (out/"results/summary.json").write_text(json.dumps(report,indent=2)+"\n")
    with (out/"results/paired_paths.csv").open("w",newline="") as f:
        writer=csv.writer(f);writer.writerow(["seed","days","arm","gross_cost_USD","offline_lower_USD","paired_headroom_USD_per_day","wall_seconds","protected_unserved_MWh","terminal_MWh"])
        for r in rec:
            for n,a in r["online"].items():
                if n=="free_fill":continue
                lb=r["offline"]["market_match9"]["cents"]/100
                writer.writerow([r["seed"],r["days"],n,a["cents"]/100,lb,(a["cents"]/100-lb)/r["days"],a["wall_s"],a["unserved_protected_MWh"],a["terminal_MWh"]])
    print(json.dumps(report["tests"]))
if __name__=="__main__":
    ap=argparse.ArgumentParser();ap.add_argument("--out",type=Path,default=HERE);verify(ap.parse_args().out)
