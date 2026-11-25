"""Exploratory replay after two failed multiplier transports. Retain every fully verified prefix."""
import sys,time
from pathlib import Path
from fractions import Fraction as F
from clique import load_primary,psd,sep
from linear import write
def investigate(path,source,out):
    start=time.perf_counter()
    h,r,cls=load_primary(path,source);u=F(r['U']);initial=F(r['L']);best=initial
    rounds=[];verified=[];pending=[];last_x=None
    for k in range(12):
        edge_start=len(h.cuts);inserted=[]
        if k:
            h.refine(last_x)
            for cl,vec in pending:
                psd(h,cl,vec);inserted.append([cl,[[str(a),str(b)] for a,b in vec]])
        info,x,y=h.lp.optimize()
        detail=dict(round=k,rows=len(h.lp.rows),columns=len(h.lp.names),eligible_dual=y is not None,**info)
        rounds.append(detail)
        if y is None:break
        val=h.lp.dual(y);assert val<=u
        best=max(best,val);detail['L']=val
        verified.append(dict(added_edge_cuts=h.cuts[edge_start:],psd=inserted,dual=y))
        if x is None or best>F(99,100)*u:break
        last_x=x;pending=sep(h,cls,x)
    write(out/'proof.json.gz',verified)
    write(out/'summary.json',dict(L=best,U=u,initial=initial,excluded=best>F(99,100)*u,trace=[v for v in rounds if 'L' in v],
             all_attempts=rounds,wall_s=time.perf_counter()-start,relative_pct=float(100*(u-best)/u)))
if __name__=='__main__':investigate(*map(Path,sys.argv[1:4]))
