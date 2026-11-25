"""Frozen-dispatch, whole-horizon rainflow revaluation. Python standard library."""
import argparse
from collections import Counter
from fractions import Fraction as F
import gzip
import hashlib
import json
import math
from pathlib import Path
import statistics as st

RATES=[50,150,300]
K=F(524,1000000)
SEEDS=[69103,69119,69143,69157,69179,69203,69221,69239]


def read(path):
    data=path.read_bytes()
    return json.loads(gzip.decompress(data) if path.suffix==".gz" else data)


def turning(path):
    z=[]
    for p in path:
        if not z or p!=z[-1]:z.append(p)
    if len(z)<3:return z
    return [z[0]]+[a for b,a,c in zip(z,z[1:],z[2:]) if (a-b)*(c-a)<0]+[z[-1]]


def stack_histogram(path):
    """Counts in units of half cycles for each integer SOC range."""
    stack=[];count=Counter()
    for h in turning(path):
        stack.append(h)
        while len(stack)>=3:
            left=abs(stack[-2]-stack[-3]);right=abs(stack[-1]-stack[-2])
            if right<left:break
            if len(stack)==3:
                count[left]+=1;stack.pop(0)
            else:
                count[left]+=2;del stack[-3:-1]
    for x,y in zip(stack,stack[1:]):count[abs(y-x)]+=1
    return count


def four_point(path):
    a=turning(path);n=Counter();i=1
    while i+2<len(a):
        left,center,right=[abs(x-y) for x,y in zip(a[i-1:i+2],a[i:i+3])]
        if center<=min(left,right):
            n[center]+=2;del a[i:i+2];i=max(1,i-2)
        else:i+=1
    for x,y in zip(a,a[1:]):n[abs(x-y)]+=1
    return n


def controls():
    tests=[([5,5,5],{}),([1,3,5],{4:1}),([2,6,2],{4:2}),([0,6,2,5,0],{6:2,3:2}),
           ([2,5,1,9,3,6,0,8,2],{3:3,4:1,8:2,9:1,6:1})]
    for x,expected in tests:
        assert stack_histogram(x)==four_point(x)==expected,(x,stack_histogram(x))
    return len(tests)


def arc_wear(q):
    return 80*abs(q*(11 if q>0 else 9))+600*int(abs(q)==2)


def analyze(plan,actual,lb):
    traj=[9];cash=0;oldwear=0;wear_cap=0
    for (q,s,bid,cost,ns,why),row in zip(plan["actions"],actual,strict=True):
        price,protected,hi,low,capacity,locked,up,down,fee=row
        assert s==traj[-1]+q and 2<=s<=11
        imp=protected+7*hi+4*low+q*(11 if q>0 else 9)
        resource=imp*price*10-fee*100*bid
        assert resource+arc_wear(q)==cost
        cash+=resource;oldwear+=arc_wear(q);traj.append(s)
        wear_cap+=max(arc_wear(a) for a in range(-capacity+up,capacity-down+1))
    assert traj[-1]==9
    cash-=45000
    assert cash+oldwear==plan["cents"] and oldwear<=wear_cap
    hist=stack_histogram(traj)
    assert hist==four_point(traj)
    assert sum(depth*n for depth,n in hist.items())==sum(abs(a-b) for a,b in zip(traj,traj[1:]))
    frac=math.fsum((cnt/2)*float(K)*(depth/12)**2.03 for depth,cnt in hist.items())
    # This exact upper bound uses 0<=depth/12<=1 and d**2.03 <= d**2.
    quad=K*sum((F(cnt,2)*F(depth,12)**2 for depth,cnt in hist.items()),F())
    assert float(quad)+1e-14>=frac
    lbnew=lb-wear_cap
    evaluated={};upper={}
    for r in RATES:
        evaluated[r]=cash/100+12000*r*frac
        exact_upper=F(cash-lbnew,100)+12000*r*quad
        upper[r]=math.ceil(exact_upper*100)/100
        assert upper[r]+1e-8>=evaluated[r]-lbnew/100>=-1e-7
    return dict(original_cents=plan["cents"],nonwear_cents=cash,original_wear_cents=oldwear,histogram_half_counts=dict(sorted(hist.items())),
                damage_fraction=frac,valued_USD=evaluated,lower_bound_new_cents=lbnew,
                upward_rounded_total_opportunity_ceiling_USD=upper,old_wear_upper_cents=wear_cap,
                quadratically_bounded_damage_fraction=[quad.numerator,quad.denominator])


def run(e,out):
    ncontrols=controls();hashes={}
    def datum(f):
        hashes[f.relative_to(e).as_posix()]=hashlib.sha256(f.read_bytes()).hexdigest()
        return read(f)
    primary=datum(e/"results/gate.json")["cases"]
    addon=datum(e/"reserve_activation_followup/results/gates.json")["cases"]
    rows=[]
    for seed in SEEDS:
        for days in (7,30):
            tag=f"{seed}_{days}.json.gz"
            r=e/"results";actual=datum(e/"inputs"/tag)["actual"]
            panels={"standby":{**datum(r/("online_"+tag)),**datum(r/("supplement_"+tag)),
                                   "price":datum(r/("baseline_"+tag))["price"]},
                    "one_call":datum(e/"reserve_activation_followup/results"/("online_"+tag))}
            for mode,plans in panels.items():
                if mode=="standby":lb=next(x for x in primary if x["seed"]==seed and x["days"]==days)["offline_cents"]["market_match9"]
                else:lb=next(x for x in addon if x["seed"]==seed and x["days"]==days)["offline_cents"]
                arms={name:analyze(plan,actual,lb) for name,plan in plans.items()}
                rows.append(dict(contract=mode,seed=seed,days=days,arms=arms))
    aggregates=[]
    for mode in panels:
        for d in (7,30):
            matched=[r["arms"] for r in rows if r["days"]==d and r["contract"]==mode]
            def effects(ref,r):
                return [(a[ref]["valued_USD"][r]-a["continuation"]["valued_USD"][r])/d for a in matched]
            cmps={}
            for ref in ("price","scenario"):
                contrasts={}
                for rate in RATES:
                    v=effects(ref,rate)
                    contrasts[rate]=dict(mean=st.mean(v),min=min(v),max=max(v),above_15=sum(i>15 for i in v))
                a=st.mean((p[ref]["nonwear_cents"]-p["continuation"]["nonwear_cents"])/100/d for p in matched)
                b=st.mean((p[ref]["damage_fraction"]-p["continuation"]["damage_fraction"])*12000/d for p in matched)
                cmps[ref]={"at_rate":contrasts,"zero_crossing_pack_USD_per_kWh":(-a/b if b else None),
                           "mean_original_contract_gain_USD_per_day":st.mean((p[ref]["original_cents"]-p["continuation"]["original_cents"])/100/d for p in matched)}
            aggregates.append(dict(contract=mode,days=d,continuation_savings_vs=cmps,
                      mean_conservative_candidate_opportunity_ceiling_USD_per_day={r:st.mean(p["continuation"]["upward_rounded_total_opportunity_ceiling_USD"][r]/d for p in matched) for r in RATES}))
    result=dict(input_SHA256=hashes,holdout_families=len(SEEDS),controls=ncontrols,
                evaluated_fixed_schedules=sum(len(x["arms"]) for x in rows),summary=aggregates,cases=rows)
    out.write_text(json.dumps(result,separators=(",",":"),allow_nan=False)+"\n")
    for s in aggregates:
        print(s["contract"],s["days"],{k:[round(v["mean"],3) for v in z["at_rate"].values()] for k,z in s["continuation_savings_vs"].items()},
              {k:round(z["zero_crossing_pack_USD_per_kWh"],2) for k,z in s["continuation_savings_vs"].items()},s["mean_conservative_candidate_opportunity_ceiling_USD_per_day"])
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--track",type=Path,required=True);p.add_argument("--out",type=Path,required=True)
    a=p.parse_args();run(a.track,a.out)
