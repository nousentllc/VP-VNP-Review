"""Exact conditional tree and cost model. All monetary arithmetic is rational."""
from functools import lru_cache
from fractions import Fraction as F
from itertools import product
from random import Random

H, D, INF = 6, 8, 10**12
ACTIONS = (0, -1, 1)

def law(kind, seed):
    """Generate ex ante regime tables only. These tables contain no realized future."""
    rng = Random(seed)
    flat = rng.randint(3, 8)
    peak = rng.randint(17, 23)
    table = []
    for t in range(H):
        pair = []
        base = [4, 3, 9, 16, 7, 6][t] + rng.randrange(3)
        for z in (0, 1):
            demand = 8 + rng.randrange(3)
            if kind == 'flat':
                price, cap, q = flat, 18, 4
            elif kind == 'time_of_use':
                price, cap, q = base + z*rng.randrange(3), 18, 3+z
            elif kind == 'ambiguous':
                price, cap, q = (peak if z else 2) + rng.randrange(4), 18, 3+2*z
            elif kind == 'rare_outage':
                price, cap, q = base//2 + z*4, (2 if z and t in (2,3,4) else 18), 1+z
            elif kind == 'positive':
                price, cap, q = [10, 12, 25, 30, 55+peak, 57+peak][t], 18, 3+z
            else:
                raise ValueError(kind)
            pair.append(dict(demand=demand,price=price,cap=cap,backup=(110 if kind=="positive" else 38+z*4),
                             q=q,wear=1))
        table.append(pair)
    return table

def mark(history):
    return int(history[-1]) if history else 0

def public(table, history):
    t, z = len(history), mark(history)
    node = table[t][z]
    forecast = None
    if t < H-1:
        q = node['q']
        children = table[t+1]
        forecast = (F(q,D), F((D-q)*children[0]['price']+q*children[1]['price'],D),
                    F((D-q)*children[0]['cap']+q*children[1]['cap'],D))
    return node, forecast

def branches(table, t, z):
    q = table[t][z]['q']
    return ((0,F(D-q,D)),(1,F(q,D)))

def arcs(s, previous):
    return [a for a in ACTIONS if 0<=s+a<=4 and abs(previous-a)<=1]

def cost(node, a):
    quantity = node['demand'] + (5 if a==1 else -4 if a==-1 else 0)
    firm = max(0, quantity-node['cap'])
    return (quantity-firm)*node['price'] + firm*node['backup'] + abs(a)*node['wear']

@lru_cache(None)
def can_end(left,s,previous):
    if left == 0:
        return s==2
    return any(can_end(left-1,s+a,a) for a in arcs(s,previous))

def soft(s):
    # Replacement-value estimate at an artificial horizon (11 dollars / MWh).
    return 11*(2-s)

def stage_actions(t,s,previous):
    return [a for a in arcs(s,previous) if can_end(H-t-1,s+a,a)]

def rolling(table, width, slope=11):
    take = {}
    @lru_cache(None)
    def search(t,z,s,previous,end):
        options=[]
        for a in stage_actions(t,s,previous):
            if t+1 == end:
                continuation = slope*(2-s-a) if end<H else 0
            else:
                continuation = sum(w*search(t+1,k,s+a,a,end)[0] for k,w in branches(table,t,z))
            options.append((cost(table[t][z],a)+continuation,a))
        return min(options,key=lambda item:item[0])
    def visit(hist,s,prev):
        t,z=len(hist),mark(hist)
        _,a = search(t,z,s,prev,min(t+width,H))
        take[hist]=a
        if t+1==H:
            return cost(table[t][z],a)
        return cost(table[t][z],a)+sum(w*visit(hist+str(k),s+a,a) for k,w in branches(table,t,z))
    return visit('',2,0), take

def leaves(table, t, z, prefix=''):
    if t==H-1:
        yield prefix,F(1)
    else:
        for digit,p in branches(table,t,z):
            for suffix,w in leaves(table,t+1,digit,prefix+str(digit)):
                yield suffix,p*w

def potential(table,t,z,s,prev):
    return min(cost(table[t][z],a)+soft(s+a) for a in stage_actions(t,s,prev))

def delta(table,t,z,s,prev,k):
    vals=[potential(table,t+1,j,s,prev) for j in (0,1)]
    return sum(w*vals[j] for j,w in branches(table,t,z))-vals[k]

def relaxation(table,k,penalty=False):
    """k common epochs, then perfect disclosure of all future marks (32 paths total)."""
    @lru_cache(None)
    def path(t, z, s, prev, suffix):
        options=[]
        for a in stage_actions(t,s,prev):
            val=cost(table[t][z],a)
            if suffix:
                nxt=int(suffix[0])
                val+=path(t+1,nxt,s+a,a,suffix[1:])
                if penalty:
                    val+=delta(table,t,z,s+a,a,nxt)
            options.append(val)
        return min(options)
    @lru_cache(None)
    def prefix(t,z,s,prev):
        if t>=k:
            return sum(w*path(t,z,s,prev,future) for future,w in leaves(table,t,z))
        options=[]
        for a in stage_actions(t,s,prev):
            nxt=0 if t+1==H else sum(w*prefix(t+1,j,s+a,a) for j,w in branches(table,t,z))
            options.append(cost(table[t][z],a)+nxt)
        return min(options)
    return prefix(0,0,2,0)

def meter_floor(table):
    tariffs={d['price'] for pair in table for d in pair}
    flat=len(tariffs)==1 and min(tariffs)>=0
    mass=[F(1),F(0)]; out=0
    for pair in table:
        for w,d in zip(mass,pair):
            value=d['price']*d['demand'] if flat else min(cost(d,a) for a in ACTIONS)
            out+=w*value
        p=sum(w*F(d['q'],8) for w,d in zip(mass,pair))
        mass=[1-p,p]
    return out

def portfolio(table):
    policies={'idle':{''.join(h):0 for t in range(H) for h in product('01',repeat=t)}}
    values={}
    for slope in (0,11,24,40):
        value,actions=rolling(table,3,slope)
        policies[str(slope)]=actions
        values[str(slope)]=value
    return policies,values
