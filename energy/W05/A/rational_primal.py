"""Post hoc exact small-model primal witnesses in the original stored-coefficient model."""
import argparse
import gzip
import json
from collections import Counter
from fractions import Fraction as Q
from pathlib import Path
import sympy as sp
from engine import HERE, arrays, model, exact_box, hs, np
from audit import exact_replay

def original_check(m,x,n,t):
    finite=lambda u:np.isfinite(u)
    def interval(v,l,u):
        return (not finite(l) or Q(float(l))<=v) and (not finite(u) or v<=Q(float(u)))
    assert len(x)==len(m.lo)
    if not all(interval(v,l,h) for v,l,h in zip(x,m.lo,m.hi)):return False
    if not all(z.denominator==1 and z in (0,1) for z in x[-n*t:]):return False
    y=[Q(0)]*len(m.lhs)
    for i,j,c in zip(m.row,m.col,m.val):y[i]+=Q(float(c))*x[j]
    return all(interval(v,l,u) for v,l,u in zip(y,m.lhs,m.rhs))

def recover(m,h):
    b=h.getBasis();assert b.valid
    def nonbasic(stat,l,u):
        if stat==hs.HighsBasisStatus.kLower:return Q(float(l))
        if stat==hs.HighsBasisStatus.kUpper:return Q(float(u))
        if stat==hs.HighsBasisStatus.kZero:return Q(0)
        raise ValueError('Unsupported basis status '+str(stat))
    cb={j:k for k,j in enumerate(j for j,s in enumerate(b.col_status) if s==hs.HighsBasisStatus.kBasic)}
    rb={i:k for k,i in enumerate(i for i,s in enumerate(b.row_status) if s!=hs.HighsBasisStatus.kBasic)}
    assert len(rb)==len(cb)
    x=[None if j in cb else nonbasic(s,m.lo[j],m.hi[j]) for j,s in enumerate(b.col_status)]
    rhs=[nonbasic(b.row_status[i],m.lhs[i],m.rhs[i]) for i in rb];co={}
    for i,j,c in zip(m.row,m.col,m.val):
        if i not in rb:continue
        k=rb[i];v=Q(float(c))
        if j in cb:co[k,cb[j]]=co.get((k,cb[j]),Q(0))+v
        else:rhs[k]-=v*x[j]
    if cb:
        mat=sp.polys.matrices.DomainMatrix.from_Matrix(sp.SparseMatrix(len(cb),len(cb),co)).to_field()
        rem=sp.polys.matrices.DomainMatrix.from_Matrix(sp.Matrix(rhs)).to_field()
        mat,rem=mat.unify(rem)
        num,den=mat.solve_den(rem)
        vec=num.to_Matrix()/mat.domain.to_sympy(den)
        for j,k in cb.items():
            q=vec[k,0];x[j]=Q(int(q.p),int(q.q))
    return x,len(cb)
def run(raw,out):
    with gzip.open(HERE/'protocol/instances.json.gz','rt') as f:cases={a['id']:arrays(a) for a in json.load(f) if a['n']==4}
    with gzip.open(raw,'rt') as f:
        rows={r['case']:r for r in map(json.loads,f) if r['case'] in cases and r['arm']=='lp_only' and r['repeat']==0}
    assert len(cases)==len(rows)==20
    results=[]
    for i,a in cases.items():
        r=rows[i];q=dict(case=i,online_hit=r['target'] is not None)
        results.append(q)
        lp=[v for v in r['witnesses'] if v['stage']=='outer_lp']
        if not lp or not r['certificates']:
            q['status']='no_recorded_LP_primal_or_dual';continue
        w=lp[-1];q['raw_physically_admissible']=w['valid']
        if not w['valid']:
            q['status']='raw_LP_rejected';continue
        n,t=a['n'],a['t'];ids=[[j] for j in range(n)]
        modes=(np.array(w['c'])>np.array(w['d'])).astype(float)
        m,_,_=model(a,ids,'mixed',modes);h=m.solver('on',1e-6)
        h.run();status=h.modelStatusToString(h.getModelStatus());q['fixed_mode_status']=status
        if status!='Optimal':q['status']='no_fixed_mode_optimum';continue
        try:
            x,dim=recover(m,h)
        except (ValueError,AssertionError,ArithmeticError) as exc:
            q['status']='basis_reconstruction_failed';q['detail']=repr(exc);continue
        orig,_,_=model(a,ids,'mixed')
        if not original_check(orig,x,n,t):
            q['status']='exact_original_check_failed';continue
        upper=sum(v*Q(float(c)) for v,c in zip(x,orig.cost))
        lower=exact_replay(orig,r['certificates'][-1]['dual'])
        assert lower<=upper
        bad=x.copy();bad[3*n*t]+=1
        assert not original_check(orig,bad,n,t)
        q.update(status='exact_witness',basis_dimension=dim,U=str(upper),L=str(lower),exact_gap=str(upper-lower),
            met_exact_gap=upper-lower<=Q(2,100000)+Q(1,1000)*max(1,abs(upper)),
            abs_reported_cost_difference=float(abs(upper-Q(float(w['cost'])))),x=[str(v) for v in x],one_MW_grid_mutation_rejected=True)
    out.mkdir(exist_ok=True,parents=True)
    with gzip.open(out/'small_exact_primal.json.gz','wt') as f:json.dump(results,f,separators=(',',':'))
    good=[z for z in results if z['status']=='exact_witness']
    (out/'small_exact_summary.json').write_text(json.dumps(dict(scope='Off-clock exploratory basis reconstruction. All 20 small cases, repeat zero of LP-only. Timed primary unchanged.',
        cases=20,statuses=dict(Counter(z['status'] for z in results)),certified_gap=sum(z['met_exact_gap'] for z in good),
        max_abs_cost_difference=max((z['abs_reported_cost_difference'] for z in good),default=None),
        max_exact_gap=float(max((Q(z['exact_gap']) for z in good),default=Q(0))),corruptions_rejected=len(good)),indent=2)+'\n')
if __name__=='__main__':
    cli=argparse.ArgumentParser();cli.add_argument('--raw',type=Path,required=True);cli.add_argument('--out',type=Path,required=True)
    a=cli.parse_args();run(a.raw,a.out)
