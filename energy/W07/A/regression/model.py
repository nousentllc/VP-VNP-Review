"""Integer-hour, quarter-MWh energy accounting and the prospective case generator."""
import hashlib
import json
import random
from fractions import Fraction
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PLAN = json.loads((ROOT / "protocol/design.json").read_text())


def generate(seed_index, hours, regime):
    seed = PLAN["seeds"][seed_index]
    ident = f"{seed}-{hours}-{regime}"
    rng = random.Random(int.from_bytes(hashlib.sha256(ident.encode()).digest(), "big"))
    cap = rng.randint(6, 11)
    start = cap // 2
    demand = [rng.randint(8, 18) for _ in range(hours)]
    price = [rng.randint(25, 55) for _ in range(hours)]
    grid = [value + rng.randint(-5, 5) for value in demand]
    charge = [rng.randint(2, 3) for _ in range(hours)]
    discharge = [rng.randint(2, 3) for _ in range(hours)]
    floor = [0] * hours
    force = [0] * hours
    ramp = rng.choice([1, 2])
    if regime == "flat_ample":
        flat = rng.choice([25, 35, 50])
        grid = [value + 10 for value in demand]
        price = [flat] * hours
    if regime == "scarce":
        grid = [max(0, value - rng.randint(0, 9)) for value in demand]
    if regime == "time_of_use":
        grid = [value + rng.randint(4, 10) for value in demand]
        price = [rng.randint(5, 20) if t % 8 < 4 else rng.randint(70, 140) for t in range(hours)]
    if regime == "negative_outage":
        for t in range(hours):
            if t % 6 < 2:
                price[t] = -rng.randint(15, 90)
                grid[t] = demand[t] + 12
            elif t % 6 == 3:
                grid[t] = rng.choice([0, 2])
                charge[t] = 0
    if regime == "forced_opposition":
        ramp = 2
        for t in range(1, hours - 1, 6):
            force[t], force[t+1] = 1, -1
            grid[t] = demand[t] + 6
            price[t] = rng.randint(70, 100)
            price[t+1] = rng.randint(5, 20)
    if regime == "tight_reserve":
        floor = [start - (t % 4 == 0) for t in range(hours)]
        grid = [value + rng.randint(-6, 6) for value in demand]
    invalid = ("missing" if (seed_index, hours, regime) == (0, 24, "tight_reserve")
               else "infeasible" if (seed_index, hours, regime) == (5, 24, "negative_outage")
               else None)
    fixed = seed_index % 2 == 0
    return dict(id=ident, n=hours, regime=regime, seed=seed, capacity=cap, initial=start,
                terminal=[start, start] if fixed else [max(floor[-1], start-2),cap],
                credit=0 if fixed else 35, wear=rng.choice([2, 4, 7]), ramp=ramp,
                demand=demand, grid=grid, price=price, charge=charge, discharge=discharge,
                floor=floor, force=force, status=invalid)


def controls():
    examples = []
    for metric, levels in [("service", [0,3,4,8]), ("cost", [0,15,20,40])]:
        for amount in levels:
            demand = 4 * ((amount + 3) // 4) if metric == "service" else 4
            examples.append((metric, amount, dict(
                id=f"control-{metric}-{amount}", n=2, regime="control", seed=None, capacity=2,
                initial=0, terminal=[0,0], credit=0, wear=0, ramp=4, demand=[0,demand],
                grid=[10,demand-amount if metric=="service" else 4], price=[0,amount if metric=="cost" else 0],
                charge=[2,2], discharge=[2,2], floor=[0,0], force=[0,0], status=None)))
    return examples


def hour(x,t,s,prev,a,fixed=None):
    c,d=max(a,0),max(-a,0)
    q=s+a
    if (not x["floor"][t] <= q <= x["capacity"] or abs(a-prev)>x["ramp"]
        or c>x["charge"][t] or d>x["discharge"][t]):
        return None
    f=x["force"][t]
    if (f>0 and a<f) or (f<0 and a>f):
        return None
    served = min(x["demand"][t],x["grid"][t]-5*c+4*d) if fixed is None else fixed[t]
    g=served+5*c-4*d
    if not 0<=served<=x["demand"][t] or not 0<=g<=x["grid"][t]:
        return None
    return q,x["demand"][t]-served,x["price"][t]*g+x["wear"]*(5*c+4*d)


def witness(x, actions, fixed=None):
    if actions is None or len(actions)!=x["n"]:
        return None
    s=x["initial"];prev=0;shed=0;cost=0;served=[]
    for t,a in enumerate(actions):
        if type(a)!=int: return None
        step=hour(x,t,s,prev,a,fixed)
        if step is None: return None
        s,loss,expense=step
        shed+=loss;cost+=expense;served.append(x["demand"][t]-loss);prev=a
    if not x["terminal"][0]<=s<=x["terminal"][1]: return None
    return dict(actions=actions,served=served,service=shed,cost=cost-4*x["credit"]*(s-x["initial"]),end=s)


def optimize(x, lo, hi, s, prev, end, after=None, fixed=None):
    """Lexicographic exact stage costs. With fixed service the first sum is constant."""
    frontier={(s,prev):(0,0,())}
    for t in range(lo,hi):
        nxt={}
        for (soc,p),(loss,cost,path) in frontier.items():
            for a in range(max(-x["discharge"][t],p-x["ramp"]),min(x["charge"][t],p+x["ramp"])+1):
                outcome=hour(x,t,soc,p,a,fixed)
                if outcome is None: continue
                q,d,k=outcome
                choice=(loss+d,cost+k,path+(a,)); key=(q,a)
                if key not in nxt or choice<nxt[key]: nxt[key]=choice
        frontier=nxt
    options=[(loss,cost-4*x["credit"]*(q-s),path) for (q,p),(loss,cost,path) in frontier.items()
             if end[0]<=q<=end[1] and (after is None or abs(after-p)<=x["ramp"])]
    return None if not options else list(min(options)[2])


def baseline(x):
    if x["status"]=="missing": return None,"withheld baseline"
    if x["status"]=="infeasible":
        a=[0]*x["n"]; a[0]=x["capacity"]+1
        assert witness(x,a) is None
        return None,"supplied witness violates limits"
    a=x["force"][:]
    w=witness(x,a)
    if w is None: return None,"seed failed physical model"
    if x["regime"]=="control": return w,None
    for offset in [0,2]:
        bounds=sorted({0,x["n"],*range(offset,x["n"],4)})
        for l,h in zip(bounds,bounds[1:]):
            start=x["initial"]+sum(a[:l])
            end=x["initial"]+sum(a[:h])
            block=optimize(x,l,h,start,a[l-1] if l else 0,
                           x["terminal"] if h==x["n"] else [end,end],a[h] if h<x["n"] else None)
            if block is None: raise ValueError("feasible block disappeared")
            a[l:h]=block
    w=witness(x,a)
    if w is None: raise ValueError("invalid local baseline")
    return w,None


def threshold(metric, upper):
    return max(Fraction(4 if metric=="service" else 80),Fraction(3,100)*abs(upper))
