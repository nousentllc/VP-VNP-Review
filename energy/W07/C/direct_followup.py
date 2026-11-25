"""Exploratory longer unrestricted solve on the unresolved full-horizon UC case."""
import json,sys,time,hashlib
from fractions import Fraction as F
from pathlib import Path
from commitment import build,upper
from linear import read,write
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'postfreeze/direct_uc'
CASE='2020-04-03_48'
def calc():
    start=time.perf_counter();lp=build(ROOT/'inputs/2020-04-03.json',48)
    original=read(ROOT/'uc_results'/CASE/'summary.json');prior=F(original['U']);floor=F(read(ROOT/'exploratory/uc_results'/CASE/'summary.json')['L'])
    t=time.perf_counter();r,x,_=lp.optimize(mixed=True,seconds=120); solved=time.perf_counter()
    candidate=None;status='no incumbent'
    if x is not None:candidate,status=upper(lp,x,r['native_objective'])
    u=lp.feasible(candidate) if candidate is not None else None
    if u is not None:assert u>=floor
    write(OUT/'witness.json.gz',dict(primal=candidate,cols=lp.names,rows=[s[0] for s in lp.rows]))
    write(OUT/'summary.json',dict(case=CASE,baseline_U=prior,checked_L=floor,new_U=u,achieved_vs_prior=prior-u if u is not None else None,
         achieved_pct=float(100*(prior-u)/prior) if u is not None else None,new_ceiling_pct=float(100*(u-floor)/u) if u else None,
         native=r,exact_recovery=status,build_s=t-start,direct_s=solved-t,verification_and_io_s=time.perf_counter()-solved,total_s=time.perf_counter()-start))
def check():
    lp=build(ROOT/'inputs/2020-04-03.json',48);w=read(OUT/'witness.json.gz');s=read(OUT/'summary.json')
    assert lp.names==w['cols'] and [r[0] for r in lp.rows]==w['rows']
    if w['primal']:
        u=lp.feasible(list(map(F,w['primal'])));assert u==F(s['new_U']) and F(s['baseline_U'])-u==F(s['achieved_vs_prior'])
    print('rational schedule checked',s['exact_recovery'],s['achieved_pct'])
if __name__=='__main__':
    if sys.argv[1]=='run':
        assert not (OUT/'summary.json').exists()
        calc()
    else:check()
