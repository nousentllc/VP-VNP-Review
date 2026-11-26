#!/usr/bin/env python3
"""Finite controls for the expanded exposition; not a proof of VP != VNP."""
def main():
    import itertools,json,math
    from fractions import Fraction as F
    def add(a,b):
        c=a.copy()
        for k,v in b.items(): c[k]=c.get(k,0)+v
        return {k:v for k,v in c.items() if v}
    def mul(a,b):
        c={}
        for i,x in a.items():
            for j,y in b.items(): c[i+j]=c.get(i+j,0)+x*y
        return {k:v for k,v in c.items() if v}
    def power(a,n):
        b={0:1}
        for _ in range(n): b=mul(b,a)
        return b
    def B(r,n):
        return {k:(-1)**k*math.comb(r+k,k)*math.comb(r,n-k) for k in range(n+1) if 0<=n-k<=r}
    count=0
    for R in range(1,9):
        for i in range(7):
            for j in range(7):
                total={}
                for r in range(R): total=add(total,{k+r:v for k,v in mul(B(r,i),B(r,j)).items()})
                total=mul(total,{0:1,1:-1})
                for n in range(R): assert total.get(n,0)==int(i==j and n==i)
                count+=1
    # Exact scalar budget and the baseline's /11 obstruction.
    a,b=F(4009,9000),F(7651,202500)
    assert 12*b-a==F(1073,135000) and b/a>F(1,12)
    k,ell,z=4,200,138;delta=F(1,4000);N=6
    slack=(F(4,18)+delta)*z-(ell*(F(4*k,81)-3*N*delta)-k*(2+delta))
    assert slack==F(15551,162000) and z<F(ell*k*2,11)
    # Laurent no-pole hypothesis and pole-rescaling protection.
    assert power({0:1,1:1,-1:1},2).get(0)==3
    for r in range(2,10):
        result=mul({-1:1}, {r:1});assert min(result)>0
    # Shared boundary, duplicate occurrences and empty products.
    assert sum(x*y for x,y in zip([1,-1],[1,0]))==1
    assert sum([1,-1])*sum([1,0])==0
    assert sum(x*y for x,y in itertools.product([2,-1],repeat=2))==1
    assert sum(x*x for x in [2,-1])==5 and math.prod([])==1
    # Modular exponent zero-test: strict range, including negative exponents.
    counter_cases=0
    for W in range(1,9):
        M=2**W
        for s in range(-M+1,M): assert (s%M==0)==(s==0);counter_cases+=1
        assert M%M==0
    # Same-witness natural division consequences for admitted positive v.
    j4_cases=0
    for v in range(2,20):
        H=272
        for multiple in [1,v,v*v,7*v*v]:
            tau=v**H*multiple
            t=tau//v**47;P=tau*v//v**H;S=v**(H-47)
            assert t*v**48<=tau*v and P*v**H<=tau*v and S*v**48<=v**H*v
            j4_cases+=1
    result={'orthogonality_congruence_cases':count,'strict_margin':str(12*b-a),'denominator_11_relaxed_slack':str(slack),'modular_counter_cases':counter_cases,'j4_integer_cases':j4_cases,'scope':'Finite algebra and boundary controls only; no new Lean or Comparator execution.'}
    print(json.dumps(result,indent=2,sort_keys=True))
if __name__=='__main__': main()
