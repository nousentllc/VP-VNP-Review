"""Fresh static AC case runs; solver suggestions are separated from rigorous checks."""
import sys
import time
import traceback
from pathlib import Path
from fractions import Fraction as F
from network import Grid
from ac_witness import witness
from ac_bound import Outer,copper
from linear import write,read
HERE=Path(__file__).resolve().parent


def run(path,d):
    clock=time.perf_counter;start=clock();g=Grid(path);t=clock()
    basics=[];eligible=[]
    for mode in ('dc','flat'):
        bstart=clock()
        try:
            trial=g.baseline(mode);u=clock()
            try:
                trial['proof']=witness(g,trial['point']);eligible.append(trial)
            except Exception as e:trial['validation_failure']=repr(e)
            trial['interval_validation_s']=clock()-u
        except Exception as e:trial=dict(mode=mode,error=repr(e),trace=traceback.format_exc())
        trial['wall_s']=clock()-bstart;basics.append(trial)
    inc=min(eligible,key=lambda r:r['proof']['U']) if eligible else None
    U=inc['proof']['U'] if inc else None
    z=clock();L,lam=copper(g);ed_s=clock()-z
    trace=[];cert=[];cutlist=[];relax_failure=None
    best=L
    if U is None or L is None or L<=F(99,100)*U:
        try:
            hull=Outer(g);seed=inc or next((r for r in basics if 'point' in r),None)
            if seed:hull.seed(seed['point'])
            for it in range(12):
                begin=clock();m,x,y=hull.lp.optimize()
                row=dict(round=it,**m,nrows=len(hull.lp.rows),ncuts=len(hull.cuts))
                if y is None:
                    trace.append(row);break
                k=clock();val=hull.lp.dual(y);row.update(L=val,dual_check_s=clock()-k)
                cert.append(dict(ncuts=len(hull.cuts),dual=y));best=max(val,best) if best is not None else val
                row['wall_s']=clock()-begin;trace.append(row)
                if U is not None and best>F(99,100)*U or x is None or it==11:break
                hull.refine(x)
            cutlist=hull.cuts
        except Exception as e:relax_failure=traceback.format_exc()
    record=dict(case=path.name,validated_starts=len(eligible),selected=inc['mode'] if inc else None,U=U,copper_L=L,price=lam,L=best,outer=trace,
                ratio_percent=float(100*(U-best)/U) if U is not None and best is not None else None,
                excluded=bool(U and best is not None and best>F(99,100)*U),relax_failure=relax_failure,
                times=dict(parse=t-start,baseline_and_validation=z-t,copper_s=ed_s,outer_with_build_and_checks=clock()-z-ed_s))
    write(d/'witnesses.json.gz',dict(starts=basics,cuts=cutlist,duals=cert))
    record['end_to_end_s']=clock()-start;write(d/'summary.json',record)
    print(path.stem,record['validated_starts'],record['ratio_percent'],len(trace),relax_failure,flush=True)


def audit(path,d):
    g=Grid(path);s=read(d/'summary.json');w=read(d/'witnesses.json.gz')
    good=[]
    for r in w['starts']:
        if 'proof' in r:
            q=witness(g,r['point'],r['proof']['selection']);assert q['U']==F(r['proof']['U'])
            good.append(q['U'])
    if good:assert min(good)==F(s['U'])
    L,lam=copper(g)
    if L is not None:assert L==F(s['copper_L'])
    if w['duals']:
        hull=Outer(g)
        for y,row in zip(w['duals'],s['outer']):
            while len(hull.cuts)<y['ncuts']:
                kind,obj,*params=w['cuts'][len(hull.cuts)]
                hull.cut(kind,tuple(obj) if isinstance(obj,list) else obj,*map(F,params))
            val=hull.lp.dual(list(map(F,y['dual'])));assert val==F(row['L'])
            if good:assert min(good)>=val
            L=val if L is None else max(L,val)
        assert hull.cuts==w['cuts'][:len(hull.cuts)]
    if good:
        r=next(r for r in w['starts'] if 'proof' in r)
        bad=r['point'].copy();bad[2*g.n]+=.01
        try:witness(g,bad,r['proof']['selection'])
        except (AssertionError,ValueError):pass
        else:raise AssertionError('1% per-unit dispatch perturbation accepted')
    if L is not None:assert L==F(s['L'])
    return s['excluded']


if __name__=='__main__':
    action,out=sys.argv[1],Path(sys.argv[2])
    for p in sorted((HERE/'inputs').glob('*.m')):
        d=out/p.stem
        if action=='run':
            if (d/'summary.json').exists():raise FileExistsError(d)
            run(p,d)
        else:print(p.stem,'audit',audit(p,d))
