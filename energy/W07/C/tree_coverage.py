"""Audit every disjunctive lower bound and terminal covering leaf against original Pyomo rows."""
import gzip,json,sys
from contextlib import redirect_stdout
from collections import Counter
from fractions import Fraction as F
from pathlib import Path
import pyomo.environ as pe
from pyomo.common.numeric_types import RegisterNumericType
from pyomo.repn import generate_standard_repn
ROOT=Path(__file__).resolve().parent
def read(path):return json.loads(gzip.decompress(path.read_bytes()) if path.suffix=='.gz' else path.read_bytes())
def verify_tree(p,T,root=ROOT):
    inp=json.loads(p.read_text(),parse_float=F);inp['time_periods']=T
    scope=dict(vars(pe),data=inp)
    code=(root/'inputs/uc_model.py').read_text()
    with redirect_stdout(sys.stderr):
        exec(code[code.index('thermal_gens = data'):code.index('print("model setup complete")')],scope)
    m=scope['m'];rows=sorted(m.component_data_objects(pe.Constraint,active=True),key=lambda a:a.name)
    cols=sorted(m.component_data_objects(pe.Var),key=lambda a:a.name); ids={id(v):j for j,v in enumerate(cols)}
    def number(x):
        z=pe.value(x)
        assert not isinstance(z,float) or z.is_integer()
        return F(z)
    def affine(e):
        rep=generate_standard_repn(e,compute_values=False)
        assert rep.is_linear()
        return number(rep.constant),[(ids[id(v)],number(a)) for v,a in zip(rep.linear_vars,rep.linear_coefs,strict=True)]
    boxes=[]
    for v in cols:
        name=v.parent_component().name
        if name in ('cg','pg','rg'):
            g=inp['thermal_generators'][v.index()[0]]
            if name=='cg':
                curve=[q['cost']-g['piecewise_production'][0]['cost'] for q in g['piecewise_production']]
                boxes.append((min(0,*curve),max(0,*curve)))
            else:boxes.append((0,g['power_output_maximum']-g['power_output_minimum']))
        else:boxes.append((number(v.lb),number(v.ub)))
    eqs=[]
    for row in rows:
        l,body,h=row.to_bounded_expression(evaluate_bounds=False)
        c,a=affine(body);eqs.append((None if l is None else number(l)-c,None if h is None else number(h)-c,a))
    offset,obj=affine(m.obj.expr)
    def bound(y,history):
        b=offset;grad=Counter(dict(obj))
        for (lo,hi,a),v in zip(eqs,y,strict=True):
            z=F(v)
            if z==0:continue
            b+=z*(lo if z>0 else hi)
            for j,c in a:grad[j]-=z*c
        for j,c in grad.items():
            if j in history:b+=c*history[j]
            else:b+=min(c*boxes[j][0],c*boxes[j][1])
        return b
    tag=f'{p.stem}_{T}'
    src=root/'uc_results'/tag
    first=read(src/'summary.json');cert=read(src/'certificate.json.gz')
    assert [r.name for r in rows]==cert['rows'] and [v.name for v in cols]==cert['columns']
    base=bound(cert['base_dual'],{});assert base==F(first['L'])
    td=root/'exploratory/uc_results'/tag
    if not td.exists():return dict(case=tag,rows=len(rows),root_checked=True,tree_nodes=0)
    tree=read(td/'tree.json.gz');values={};children={i:[] for i in range(len(tree))}
    for i,n in enumerate(tree):
        history=dict(n['branch']);assert len(history)==len(n['branch'])
        assert all(cols[j].is_binary() and v in [0,1] for j,v in history.items())
        parent=n['parent']
        if i==0:assert parent is None and not history;floor=base
        else:assert 0<=parent<i;children[parent].append(i);floor=values[parent]
        if n['dual'] is not None:floor=max(floor,bound(n['dual'],history))
        values[i]=floor;assert floor==F(n['L'])
    for i,cs in children.items():
        if cs:
            j=tree[i]['split']
            assert j not in dict(tree[i]['branch'])
            assert sorted(tree[k]['branch'] for k in cs)==[tree[i]['branch']+[[j,b]] for b in [0,1]]
    leaves=[i for i,cs in children.items() if not cs]
    mass=sum(F(1,2**len(tree[i]['branch'])) for i in leaves)
    assert mass==1
    combined=max(F(first['strongest_L']),min(values[i] for i in leaves));assert combined==F(read(td/'summary.json')['L'])
    return dict(case=tag,rows=len(rows),tree_nodes=len(tree),leaves=len(leaves),assigned_binary_cube_mass=str(mass),checked_lower=str(combined))
if __name__=='__main__':
    RegisterNumericType(F)
    print(json.dumps([verify_tree(p,t) for p in sorted((ROOT/'inputs').glob('20*.json')) for t in (24,48)],indent=2))
