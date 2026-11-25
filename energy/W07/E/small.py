"""Exact finite economics with conditional call probability 1/2 and an independent explicit tail enumeration."""
from fractions import Fraction as F
from functools import lru_cache
from itertools import product
from collections import Counter
from decimal import Decimal, localcontext, ROUND_HALF_UP
import numpy as np
from independent import ST,IX,branches
from model import kernels
from historical.rainflow import stack_histogram,four_point


def wear_prices(rate):
    # Frozen cent grid per *half cycle*. The ensuing objective is rational, including expectation.
    with localcontext() as ctx:
        ctx.prec=48
        return {m:int((Decimal(12000*rate*100)*Decimal('0.000524')/2*(Decimal(m)/12)**Decimal('2.03')).to_integral_value(rounding=ROUND_HALF_UP)) for m in range(1,10)}


def revalue(path,prices):
    hist=stack_histogram(path);assert hist==four_point(path)
    assert sum(i*n for i,n in hist.items())==sum(abs(i-j) for i,j in zip(path,path[1:]))
    return sum(n*prices[i] for i,n in hist.items())


def small():
    # Explicit finite toy separate from the 72-hour contract; includes a published recovery hour.
    signs=[1,1,-1,0,0]; prices=[15,120,160,60,30]; ps=[[2]]*5; n=len(signs)
    v,m=kernels(n,2,signs,ps)
    z=wear_prices(150)
    def terminal(hist,mode):return -45000+(revalue(hist,z) if mode=='rain' else 0)
    def step(a,t,enabled,call,mode):
        dg=a*(11 if a>0 else 9)
        return (34+dg)*prices[t]*10-800*int(enabled)-350*int(call)+(abs(dg)*80+600*(abs(a)==2) if mode=='linear' else 0)
    def solve(mode):
        decisions={}
        @lru_cache(None)
        def visit(t,s,p,b,hist):
            if t==n: return F(terminal(hist,mode)) if s==9 else None
            d=signs[t];cs=(0,d) if d and b else (0,)
            options=[]
            for q in np.flatnonzero(m[t,2,b,IX[s,p]])-2:
                q=int(q);outcomes=[]
                for c in cs:
                    a=q+c;after=s+a
                    val=visit(t+1,after,a,b-int(c!=0),hist+(after,))
                    if val is None:break
                    outcomes.append(val+step(a,t,d!=0,c!=0,mode))
                if len(outcomes)==len(cs):options.append((sum(outcomes,F())/len(cs),q))
            if not options:return None
            value,q=min(options);decisions[(t,s,p,b,hist)]=q
            return value
        optimal=visit(0,9,0,2,(9,));return optimal,decisions
    def evaluate(policy,mode):
        # Forward path replay enumerates every call sequence and revalues each full path on original weights.
        records=[]
        def go(t,s,p,b,hist,mass,total):
            if t==n:
                assert s==9
                records.append((mass,total+terminal(hist,mode)));return
            q=policy[t,s,p,b,hist];d=signs[t];cs=[0,d] if b and d else [0]
            valid={qq:(j,j1) for qq,j,j1 in branches(IX[s,p],2,d)}
            assert q in valid
            for c in cs:
                a=q+c;s1=s+a
                assert (valid[q][1] if c else valid[q][0])==IX[s1,a]
                go(t+1,s1,a,b-int(c!=0),hist+(s1,),mass/len(cs),total+step(a,t,d!=0,c!=0,mode))
        go(0,9,0,2,(9,),F(1),0)
        assert sum((r[0] for r in records),F())==1
        return sum((w*c for w,c in records),F()),len(records)
    old,pol=solve('linear');rain,pr=solve('rain');revalued,leaves=evaluate(pol,'rain')
    assert evaluate(pol,'linear')[0]==old and evaluate(pr,'rain')[0]==rain and revalued>=rain
    # Separate top-down exact enumeration of feasible schedules, no kernel input and no memoization.
    def independent(t,s,previous,b,path,mode):
        if t==n: return F(-45000+(sum(n*z[d] for d,n in four_point(path).items()) if mode=='rain' else 0)) if s==9 else None
        d=signs[t];pool=[]
        for q,j,other in branches(IX[s,previous],2,d):
            pairs=[(q,j)]+([(q+d,other)] if d and b else [])
            if any(x is None for a,x in pairs):continue
            subtotal=F()
            for a,nxt in pairs:
                ns,np0=ST[nxt];c=a-q;tail=independent(t+1,ns,np0,b-int(bool(c)),path+[ns],mode)
                if tail is None:break
                ac=11*max(0,a)+9*min(0,a)
                money=(34+ac)*prices[t]*10-800*bool(d)-350*bool(c)
                if mode=='linear':money+=80*abs(ac)+600*(abs(a)==2)
                subtotal+=money+tail
            else:pool.append(subtotal/len(pairs))
        return min(pool) if pool else None
    assert independent(0,9,0,2,[9],'linear')==old
    assert independent(0,9,0,2,[9],'rain')==rain
    return dict(prices=prices,load_deciMWh=34,signs=signs,budget=2,
        call_probability_given_eligible_and_remaining='1/2',leaves=leaves,wear_per_half_cycle_150_cents=z,
        linear_exact_optimal_expected_cents=str(old),fixed_linear_policy_rain_expected_cents=str(revalued),
        reoptimized_rain_expected_cents=str(rain),saving_from_reoptimization_cents=str(revalued-rain),
        linear_first_q=pol[0,9,0,2,(9,)],rain_first_q=pr[0,9,0,2,(9,)],cross_checked_complete_tree=True)
