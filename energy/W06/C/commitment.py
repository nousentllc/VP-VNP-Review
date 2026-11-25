"""Evaluate exact LP certificates and fixed-commitment rational upper witnesses on PGLib-UC."""
import sys
import json
import time
import contextlib
import io
from fractions import Fraction as F
from pathlib import Path
import pyomo.environ as pe
from pyomo.repn import generate_standard_repn
from pyomo.common.numeric_types import RegisterNumericType
RegisterNumericType(F)
from linear import Linear,write,read
HERE=Path(__file__).resolve().parent


def build(path,periods):
    with path.open() as f: data=json.load(f,parse_float=F)
    data['time_periods']=periods
    # The official model only indexes the declared number of periods, starting at original t=1.
    ref=(HERE/'inputs/uc_model.py').read_text()
    model=ref.split('print("building model")')[1].split('print("model setup complete")')[0]
    scope=dict(vars(pe),data=data,thermal_gens=data['thermal_generators'],renewable_gens=data['renewable_generators'],
          time_periods={t+1:t for t in range(periods)},
          gen_startup_categories={g:list(range(len(v['startup']))) for g,v in data['thermal_generators'].items()},
          gen_pwl_points={g:list(range(len(v['piecewise_production']))) for g,v in data['thermal_generators'].items()})
    exec(compile(model,'pglib_uc_model','exec'),scope)
    m=scope['m']; lp=Linear(); columns={}
    for v in sorted(m.component_data_objects(pe.Var),key=lambda var:var.name):
        field=v.parent_component().local_name
        lo,hi=v.lb,v.ub
        if field in ('cg','pg','rg'):
            g=data['thermal_generators'][v.index()[0]]
            if field=='cg':
                differences=[point['cost']-g['piecewise_production'][0]['cost'] for point in g['piecewise_production']]
                lo,hi=min([0]+differences),max([0]+differences)
            else: lo,hi=0,g['power_output_maximum']-g['power_output_minimum']
        columns[id(v)]=lp.var(v.name,lo,hi,integer=v.is_binary())
    def linearize(expr):
        rep=generate_standard_repn(expr)
        assert rep.is_linear()
        return {columns[id(v)]:F(c) for c,v in zip(rep.linear_coefs,rep.linear_vars)},F(rep.constant or 0)
    for row in sorted(m.component_data_objects(pe.Constraint,active=True),key=lambda con:con.name):
        lo,body,hi=row.to_bounded_expression(evaluate_bounds=True)
        co,off=linearize(body)
        lp.row(row.name,co,None if lo is None else F(lo)-off,None if hi is None else F(hi)-off)
    co,lp.offset=linearize(m.obj.expr)
    for j,c in co.items(): lp.cost[j]=c
    return lp


def upper(lp,x,obj):
    import z3
    def exact(v): return z3.RealVal(str(v))
    s=z3.SolverFor('QF_LRA');s.set(timeout=40000)
    # Fix the incumbent binaries and restrict its interpolation support for a primal-only search.
    # Eliminate fixed candidates as constants to reduce exact simplex work.
    vals=[]; variables={}
    for i,((lo,hi),value,integer,name) in enumerate(zip(lp.box,x,lp.integer,lp.names)):
        if integer: val=F(round(value))
        elif lo==hi or abs(float(lo)-value)<1e-7: val=lo
        elif abs(float(hi)-value)<1e-7: val=hi
        else:
            v=z3.Real('x'+str(i));variables[i]=v
            s.add(v>=exact(lo),v<=exact(hi));val=None
        vals.append(val)
    def expr(row):
        fixed=F(0); terms=[]
        for j,a in row.items():
            if j in variables: terms.append(exact(a)*variables[j])
            else: fixed+=a*vals[j]
        return z3.Sum(terms)+exact(fixed)
    for _,co,lo,hi in lp.rows:
        lhs=expr(co)
        if lo==hi: s.add(lhs==exact(lo))
        else:
            if lo is not None:s.add(lhs>=exact(lo))
            if hi is not None:s.add(lhs<=exact(hi))
    limit=F(str(round(obj,4)))+F(1,100)
    cost=expr({j:c for j,c in enumerate(lp.cost) if c})+exact(lp.offset)
    s.add(cost<=exact(limit))
    status=s.check()
    if status!=z3.sat:return None,str(status)
    model=s.model()
    for j,v in variables.items():
        q=model.eval(v,model_completion=True);vals[j]=F(q.numerator_as_long(),q.denominator_as_long())
    lp.feasible(vals)
    return vals,'sat'


def run(path,T,out):
    clock=time.perf_counter; start=clock()
    lp=build(path,T);t=clock()
    lr,lpx,y=lp.optimize();assert y is not None
    L=lp.dual(y); lt=clock()
    mr,x,_=lp.optimize(mixed=True);mt=clock()
    U=None;exact=None;repair='no incumbent'
    if x is not None:
        exact,repair=upper(lp,x,mr['native_objective'])
        if exact is not None:U=lp.feasible(exact)
    ut=clock();splits=[];lower=L
    if U is not None and L <= F(99,100)*U:
        cand=[j for j,n in enumerate(lp.names) if n.startswith('ug[') and 1e-7<lpx[j]<1-1e-7]
        if cand:
            j=min(cand,key=lambda j:abs(lpx[j]-.5))
            for value in [0,1]:
                old=lp.box[j];lp.box[j]=(F(value),F(value))
                rr,_,yy=lp.optimize()
                splits.append(dict(j=j,name=lp.names[j],value=value,solver=rr,y=yy,L=lp.dual(yy) if yy is not None else None))
                lp.box[j]=old
            if all(s['L'] is not None for s in splits):lower=max(L,min(s['L'] for s in splits))
    r=dict(case=path.name,horizon=T,n=len(lp.names),rows=len(lp.rows),integers=sum(lp.integer),lp=lr,milp=mr,
        rational_recovery=repair,L=L,strongest_L=lower,U=U,ratio_percent=float(100*(U-lower)/U) if U else None,
        excluded=bool(U and lower>F(99,100)*U),times=dict(build=t-start,lp_and_check=lt-t,full_milp=mt-lt,upper_reconstruction=ut-mt,branch_check=clock()-ut),
        native_gap_percent=(100*(mr['native_objective']-mr['native_dual_bound'])/mr['native_objective'] if x is not None and mr['native_dual_bound'] is not None else None))
    write(out/'certificate.json.gz',dict(columns=lp.names,rows=[r[0] for r in lp.rows],primal=exact,native_primal=x,base_dual=y,splits=splits))
    r['end_to_end_s']=clock()-start;write(out/'summary.json',r)
    print(path.name,T,repair,r['ratio_percent'],r['end_to_end_s'],flush=True)


def audit(path,T,out):
    lp=build(path,T);r=read(out/'summary.json');cert=read(out/'certificate.json.gz')
    assert lp.names==cert['columns'] and [r[0] for r in lp.rows]==cert['rows']
    val=lp.dual(list(map(F,cert['base_dual'])));assert val==F(r['L'])
    split_values=[]
    for arm in cert['splits']:
        j=arm['j'];old=lp.box[j];lp.box[j]=(F(arm['value']),F(arm['value']))
        if arm['y'] is not None:
            v=lp.dual(list(map(F,arm['y'])));assert v==F(arm['L']);split_values.append(v)
        lp.box[j]=old
    if len(split_values)==2:
        assert [s['value'] for s in cert['splits']]==[0,1] and len(set(s['j'] for s in cert['splits']))==1 and lp.integer[j]
        val=max(val,min(split_values))
    assert val==F(r['strongest_L'])
    if cert['primal']:
        x=list(map(F,cert['primal']));u=lp.feasible(x);assert u==F(r['U']) and u>=val
        i=lp.names.index(next(n for n in lp.names if n.startswith('pg[')))
        x[i]+=1
        try: lp.feasible(x)
        except ValueError: pass
        else: raise AssertionError('changed dispatch accepted')
    return r['excluded']


if __name__=='__main__':
    action,out=sys.argv[1],Path(sys.argv[2])
    for path in sorted((HERE/'inputs').glob('20*.json')):
        for T in (8,24):
            dest=out/f'{path.stem}_{T}'
            if action=='run':
                if (dest/'summary.json').exists(): raise FileExistsError(dest)
                run(path,T,dest)
            else: print(path.name,T,'audit',audit(path,T,dest))
