"""Run original-scale post hoc W05 concatenations with exact online fill and economic lower witnesses."""
import argparse
import gzip
import hashlib
import json
import time
import zipfile
from fractions import Fraction as F
from pathlib import Path

import numpy as np
from scipy.optimize import linprog
from scipy.sparse import coo_matrix

from replay import reconstruct

def pair(x):return [x.numerator,x.denominator]


def matrix(rows,n):
    ii=[];jj=[];v=[]
    for i,row in enumerate(rows):
        for j,value in row:
            ii.append(i);jj.append(j);v.append(float(value))
    return coo_matrix((v,(ii,jj)),shape=(len(rows),n)).tocsr()


def case(case_list,p,receipt=False):
    clock=time.perf_counter_ns();initial=F(p["initial"]);prev=F(p["previous"])
    ec=F(p["eta_c"]);dd=F(1./p["eta_d"]);eq=[];b=[];ineq=[];u=[];bounds=[];x=[];boundaries=[]
    for k,c in enumerate(case_list):
        original=dict(p,initial=initial,previous=prev)
        path=reconstruct(c,original)
        for t,row in enumerate(path):
            g,ch,ds,sh,soc=row;idx=24*k+t;j=4*idx
            eq.append([(j,1),(j+1,-1),(j+2,1)]);b.append(F(c["load"][t])-sh)
            eq.append([(j+3,1),(j+1,-ec),(j+2,dd)]+([(j-1,-1)] if idx else []))
            b.append(F(0) if idx else F(p["initial"]))
            ramp=[(j,1)]+([(j-4,-1)] if idx else [])
            ineq.extend([ramp,[(a,-h) for a,h in ramp]])
            history=F(0) if idx else F(p["previous"])
            u.extend([F(p["ramp"])+history,F(p["ramp"])-history])
            power=F(p["power"])*int(c["available"][t])
            bounds.extend([(0,F(p["grid_cap"])),(0,power),(0,max(0,power-F(c["reserve"][t]))),(F(c["floor"][t]),F(p["energy"]))])
            x.extend([g,ch,ds,soc])
        initial=path[-1][4];prev=path[-1][0];boundaries.append([pair(initial),pair(prev)])
    assert all(sum(x[j]*v for j,v in row)==rhs for row,rhs in zip(eq,b))
    assert all(sum(x[j]*v for j,v in row)<=rhs for row,rhs in zip(ineq,u))
    assert all(l<=v<=h for v,(l,h) in zip(x,bounds))
    ae=matrix(eq,len(x));ai=matrix(ineq,len(x));coef=[50,10,10,0]*(len(x)//4);coef[-1]=-50
    upper=sum(t*v for t,v in zip(coef,x))
    r=dict(ids=[c["id"] for c in case_list],days=k+1,multiday_terminal_grid_soc=["soc","grid"],
           boundary_states=boundaries,fill_cost=pair(upper),arms={})
    for arm in ["same_stock","min_stock"]:
        box=list(bounds)
        if arm=="same_stock":box[-1]=(x[-1],x[-1])
        lp=linprog(coef,A_eq=ae,b_eq=np.array(b,dtype=float),A_ub=ai,b_ub=np.array(u,dtype=float),
                   bounds=np.array(box,dtype=float),method="highs")
        if not lp.success:r["arms"][arm]={"failed":lp.message};continue
        y=list(map(F,lp.eqlin.marginals));z=[min(0,F(v)) for v in lp.ineqlin.marginals]
        red=list(map(F,coef));constant=F(0)
        for row,rhs,weight in zip(eq+ineq,b+u,y+z):
            constant+=weight*rhs
            for j,v in row:red[j]-=weight*v
        lower=constant+sum(min(lo*c,hi*c) for c,(lo,hi) in zip(red,box))
        assert lower<=upper
        r["arms"][arm]=dict(lower=pair(lower),gap=pair(upper-lower),daily_gap=float((upper-lower)/len(case_list)),
            eq_duals=[pair(i) for i in y],le_duals=[pair(i) for i in z],
            numeric_cost=float(lp.fun),numeric_max_mutual_charge=float(np.minimum(lp.x[1::4],lp.x[2::4]).max()))
    r["seconds"]=time.perf_counter_ns()/1e9-clock/1e9
    return r


def run(w05,out):
    with zipfile.ZipFile(w05) as ar:
        p=json.loads(gzip.decompress(ar.read("Energy_Explorations/W05/E/inputs/holdout.json.gz")))
    cases=[]
    for panel in ("primary","alternative"):
        for regime in ("base","outage_reserve"):
            rows=sorted([r for r in p["cases"] if r["panel"]==panel and r["regime"]==regime],key=lambda x:x["seed"])
            half=len(rows)//2
            for start in (0,half):
                for days in ([7,30] if panel=="primary" else [7]):
                    paths=rows[start:start+days]
                    try:result=case(paths,p["parameters"])
                    except (ValueError,AssertionError) as e:
                        result=dict(ids=[r["id"] for r in paths],days=days,error=type(e).__name__+" "+str(e))
                    result.update(panel=panel,regime=regime,block=start);cases.append(result)
    out.write_bytes(gzip.compress(json.dumps(cases,separators=(",",":")).encode(),mtime=0))
    print([(r["panel"],r["regime"],r["days"],r.get("error") or [round(a["daily_gap"],3) if "daily_gap" in a else "LP failed" for a in r["arms"].values()]) for r in cases])
if __name__=="__main__":
    ap=argparse.ArgumentParser();ap.add_argument("w05",type=Path);ap.add_argument("out",type=Path);a=ap.parse_args();run(a.w05,a.out)
