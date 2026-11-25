"""Stand-alone exact replay. No imports from the model, numerical optimizer or policy."""
from fractions import Fraction as F
from functools import lru_cache
from itertools import product

BITS = tuple(''.join(x) for x in product('01',repeat=5))

def audit(tables, kind, actions=None, proof=None):
    leaf_weights=[]
    for suffix in BITS:
        prob=F(1)
        for t,b in enumerate(suffix):
            mark=int(suffix[t-1]) if t else 0
            q=F(tables[t][mark]['q'],8)
            prob *= q if b=='1' else 1-q
        leaf_weights.append(prob)
    assert sum(leaf_weights)==1 and min(leaf_weights)>0
    def node(t,z,s,prev,a):
        d=tables[t][z]; end=s+a
        if not (0<=end<=4 and abs(a-prev)<=1):
            return None
        quantity=d['demand']+5*max(0,a)-4*max(0,-a)
        assert quantity>=0 and d['backup']>d['price']
        grid=min(quantity,d['cap'])
        return d['wear']*abs(a)+grid*d['price']+(quantity-grid)*d['backup']
    if kind=='analytic':
        prices=[d['price'] for pair in tables for d in pair]
        flat=min(prices)==max(prices) and min(prices)>=0
        out=0
        for leaf,weight in zip(BITS,leaf_weights):
            total=0
            for t in range(6):
                z=int(leaf[t-1]) if t else 0
                d=tables[t][z]
                total+=d['demand']*d['price'] if flat else min(node(t,z,2,0,a) for a in (-1,0,1))
            out+=weight*total
        return out
    if kind=='policy':
        observed=set(); costs=[]
        for leaf in BITS:
            s,prev=2,0; total=0
            for t in range(6):
                h=leaf[:t]; observed.add(h)
                a=actions[h]
                assert type(a) is int and a in (-1,0,1)
                term=node(t,int(h[-1]) if h else 0,s,prev,a)
                assert term is not None
                total+=term; s+=a; prev=a
            assert s==2
            costs.append(total)
        assert set(actions)==observed
        return sum(v*p for v,p in zip(costs,leaf_weights))
    # Feasibility-only backward set, built across all inventory and ramp states.
    good={6:{(2,r) for r in (-1,0,1)}}
    for t in reversed(range(6)):
        good[t]={(s,r) for s in range(5) for r in (-1,0,1) if any(
            abs(a-r)<=1 and (s+a,a) in good[t+1] for a in (-1,0,1))}
    @lru_cache(None)
    def potential(t,z,s,r):
        values=[]
        for a in (-1,0,1):
            v=node(t,z,s,r,a)
            if v is not None and (s+a,a) in good[t+1]:
                values.append(v+11*(2-s-a))
        return min(values)
    centered=0
    @lru_cache(None)
    def corrections(t,z,s,a):
        nonlocal centered
        p=F(tables[t][z]['q'],8)
        diff=potential(t+1,1,s,a)-potential(t+1,0,s,a)
        residuals=(p*diff,-(1-p)*diff)
        assert (1-p)*residuals[0]+p*residuals[1]==0
        if proof is not None:
            proof[f'{t},{z},{s},{a}']=list(map(str,residuals))
        centered+=1
        return residuals
    if kind=='center_count':
        for t in range(5):
            for z in ((0,) if t==0 else (0,1)):
                for s,r in good[t]:
                    for a in (-1,0,1):
                        if abs(r-a)<=1 and (s+a,a) in good[t+1]:
                            corrections(t,z,s+a,a)
        return centered
    split={'PF':0,'prefix1':1,'prefix3':3,'causal':6,'penalty':0}[kind]
    @lru_cache(None)
    def clair(leaf,t,s,prev):
        if t==6:
            return 0
        z=int(leaf[t-1]) if t else 0
        values=[]
        for a in (-1,0,1):
            v=node(t,z,s,prev,a)
            if v is None or (s+a,a) not in good[t+1]:
                continue
            if kind=='penalty' and t<5:
                v+=corrections(t,z,s+a,a)[int(leaf[t])]
            values.append(v+clair(leaf,t+1,s+a,a))
        return min(values)
    @lru_cache(None)
    def choose(h,s,prev):
        t=len(h); z=int(h[-1]) if h else 0
        paths=[i for i,b in enumerate(BITS) if b.startswith(h)]
        mass=sum(leaf_weights[i] for i in paths)
        if t==split:
            return sum(leaf_weights[i]*clair(BITS[i],t,s,prev) for i in paths)
        scores=[]; payoffs={}
        for a in (-1,0,1):
            v=node(t,z,s,prev,a)
            if v is None or (s+a,a) not in good[t+1]:
                continue
            future=0 if t==5 else choose(h+'0',s+a,a)+choose(h+'1',s+a,a)
            score=mass*v+future
            scores.append(score); payoffs[str(a)]=str(score)
        if proof is not None:
            proof[f'{h},{s},{prev}']={'mass':str(mass),'weighted_Q':payoffs}
        return min(scores)
    return choose('',2,0)

def reject_leak(records):
    """(records are public history, equal endogenous inventory and ramp, proposed action)."""
    seen={}
    for h,s,r,a in records:
        key=(h,s,r)
        if key in seen and seen[key]!=a:
            raise ValueError('different actions for identical observable history and state')
        seen[key]=a

def controls():
    # Before a fair binary signal, preparation costs 10; omission later costs 50 in high state.
    # Adapted preparation is 10; clairvoyance spends 10 only on high; refusing prep costs 25.
    root_options=[F(25),F(10)]
    exact=min(root_options); restricted=root_options[0]
    pf=(min(0,10)+min(50,10))/F(2)
    assert pf==5 and exact==10 and restricted-exact==15
    assert not restricted-exact<15
    assert restricted-restricted<15
    # +20 if prepared has empirical mean zero on never-prepare but raises true optimum from 10 to 25.
    invalid_center_on_baseline=min(root_options[0],root_options[1]+20)
    assert invalid_center_on_baseline==25 and invalid_center_on_baseline>exact
    reject_leak([('',2,0,0),('',2,0,0)])
    try:
        reject_leak([('',2,0,-1),('',2,0,1)])
    except ValueError:
        pass
    else:
        raise AssertionError('leaked future accepted')
    # One eligible, one missing family. Reporting full mass as excluded is invalid.
    all_weights=(F(1,3),F(2,3))
    assert sum(all_weights)==1 and all_weights[0]!=1
    return dict(pf=5,causal=10,baseline=25,gain=15,equality_retained=True,
                restricted_false_exclusion=True,fitted_penalty_false_exclusion=True,
                leaked_action_rejected=True,missing_baseline_excluded_mass='1/3',unknown_mass='2/3')
