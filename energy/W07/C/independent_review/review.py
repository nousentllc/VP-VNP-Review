"""Second implementation checks selected AC residuals and the exact UC witnesses and LP certificates."""
from collections import Counter
from fractions import Fraction as F
from pathlib import Path
import cmath
import gzip
import json
import math
import re
from hashlib import sha256

ROOT=Path(__file__).resolve().parent.parent
OUT=None


def read(p):
    return json.loads(gzip.decompress(p.read_bytes()) if p.suffix==".gz" else p.read_bytes())


def ac(p):
    m={}
    for name in ["bus","gen","gencost","branch"]:
        table=re.search(r"mpc\."+name+r"\s*=\s*\[([^\]]*)\]",p.read_text(),re.S)[1]
        table=re.sub("%[^\n]*","",table)
        m[name]=[list(map(F,row.split())) for row in table.split(';') if row.strip()]
    M=F(re.search(r'mpc.baseMVA\s*=\s*([.\d]+)',p.read_text())[1])
    gens=[(g,c) for g,c in zip(m["gen"],m["gencost"]) if g[7]>0]
    branches=[x for x in m["branch"] if x[10]>0]
    b=m["bus"];n=len(b);k=len(gens);ix={x[0]:i for i,x in enumerate(b)}
    path=ROOT/"ac_results"/p.stem;sol=read(path/"summary.json");w=read(path/"witnesses.json.gz")
    results=[]
    for r in w["starts"]:
        if "proof" not in r: continue
        a=r["point"];V=[complex(u,v) for u,v in zip(a[:n],a[n:2*n])]
        S=[complex(float(q[2]),float(q[3]))+complex(float(q[4]),-float(q[5]))*(abs(v)**2) for q,v in zip(b,V)]
        max_flow=0.;max_angle=0.;min_voltage_margin=1.
        for row,v in zip(b,V):min_voltage_margin=min(min_voltage_margin,abs(v)-float(row[12]),float(row[11])-abs(v))
        for br in branches:
            i,j=ix[br[0]],ix[br[1]]
            src,dst=V[i],V[j]
            tap=float(br[8] or 1)*cmath.exp(1j*math.radians(float(br[9])))
            imped=complex(float(br[2]),float(br[3]))
            # Explicit ideal transformer and series current; no Ybus code reuse.
            left=src/tap
            series=(left-dst)/imped
            charging=1j*float(br[4])/2
            Sfrom=left*(series+left*charging).conjugate()*float(M)
            Sto=dst*(-series+dst*charging).conjugate()*float(M)
            S[i]+=Sfrom;S[j]+=Sto
            if br[5]>0:max_flow=max(max_flow,abs(Sfrom)/float(br[5]),abs(Sto)/float(br[5]))
            angle=math.degrees(cmath.phase(src)-cmath.phase(dst))
            max_angle=max(max_angle,angle-float(br[12]),float(br[11])-angle)
        fuel=0.;max_gg=0.
        for j,(g,c) in enumerate(gens):
            pp=a[2*n+j]*float(M);qq=a[2*n+k+j]*float(M)
            S[ix[g[0]]]-=complex(pp,qq);fuel+=float(c[4])*pp**2+float(c[5])*pp+float(c[6])
            max_gg=max(max_gg,float(g[9])-pp,pp-float(g[8]),float(g[4])-qq,qq-float(g[3]))
        mismatch=max(abs(z) for z in S)
        assert mismatch<1e-4 and max_gg<1e-5 and max_angle<1e-5 and max_flow<1.000001 and min_voltage_margin>=-1e-6
        assert abs(fuel-float(F(r['proof']['U'])))<max(1e-3,abs(fuel)*1e-7)
        assert F(r['proof']['residual_norm'])+F(r['proof']['lipschitz_norm'])*F(r['proof']['radius'])<F(r['proof']['radius'])
        results.append(dict(mode=r['mode'],max_bus_complex_MVA_mismatch=mismatch,max_thermal_ratio=max_flow,
                            max_angle_violation_deg=max_angle,max_generator_violation=max_gg,min_voltage_margin=min_voltage_margin,
                            midpoint_cost_vs_rigorous_upper=fuel-float(F(r['proof']['U']))))
    if sol['price'] is not None:
        lam=F(sol['price'])
        assert lam>=0 and min(q[4] for q in b)>=0 and min(br[2] for br in branches)>=0
        z=lam*sum(q[2] for q in b)
        for g,c in gens:
            a,h,k=c[4:7];lo=g[9];hi=g[8]
            cand=[lo,hi]
            if a: cand.append(max(lo,min(hi,(lam-h)/(2*a))))
            z+=min(a*v*v+(h-lam)*v+k for v in cand)
        assert z==F(sol['copper_L'])
    return dict(input=p.name,modes=results,copper_checked=sol['price'] is not None)


def uc(p,T):
    import pyomo.environ as pe
    from pyomo.common.numeric_types import RegisterNumericType
    RegisterNumericType(F)
    inp=json.loads(p.read_text(),parse_float=F);inp["time_periods"]=T
    code=(ROOT/"inputs/uc_model.py").read_text()
    scope=dict(vars(pe),data=inp)
    exec(code[code.index('thermal_gens = data'):code.index('print("model setup complete")')],scope)
    m=scope['m']; rows=sorted(m.component_data_objects(pe.Constraint,active=True),key=lambda c:c.name);cols=sorted(m.component_data_objects(pe.Var),key=lambda v:v.name)
    cert=read(ROOT/'uc_results'/f'{p.stem}_{T}'/'certificate.json.gz');summ=read(ROOT/'uc_results'/f'{p.stem}_{T}'/'summary.json')
    assert cert["columns"]==[v.name for v in cols] and cert["rows"]==[row.name for row in rows]
    box=[]
    for v in cols:
        name=v.parent_component().name
        if name in ['cg','pg','rg']:
            g=inp['thermal_generators'][v.index()[0]]
            if name=='cg':
                costs=[q['cost']-g['piecewise_production'][0]['cost'] for q in g['piecewise_production']]
                box.append((min(0,*costs),max(0,*costs)))
            else:box.append((0,g['power_output_maximum']-g['power_output_minimum']))
        else:box.append((v.lb,v.ub))
    ids={id(v):j for j,v in enumerate(cols)}
    def numeric(x):
        z=pe.value(x)
        assert not (isinstance(z,float) and F(z).denominator>1),("noninteger float",z)
        return F(z)
    def linear(node,factor,terms):
        if id(node) in ids:
            terms[ids[id(node)]]+=factor
            return 0
        if not pe.is_potentially_variable(node): return numeric(node)*factor
        name=type(node).__name__; args=node.args
        if name in ('LinearExpression','SumExpression'):
            return sum(linear(a,factor,terms) for a in args)
        if name in ('MonomialTermExpression','ProductExpression'):
            left,right=args
            if not pe.is_potentially_variable(left): return linear(right,factor*numeric(left),terms)
            return linear(left,factor*numeric(right),terms)
        if name=='NegationExpression':return linear(args[0],-factor,terms)
        raise ValueError(name)
    def dual(ys,split=None):
        g=Counter();d=linear(m.obj.expr,F(1),g)
        assert len(rows)==len(ys)
        for row,y in zip(rows,map(F,ys)):
            if not y:continue
            lo,body,hi=row.to_bounded_expression(evaluate_bounds=False); d+=y*numeric(lo if y>0 else hi)+linear(body,-y,g)
        for j in range(len(cols)):
            l,h=box[j] if not split or j!=split[0] else (split[1],split[1])
            d+=min(l*g[j],h*g[j])
        return d
    base=dual(cert['base_dual']);assert base==F(summ['L'])
    strongest=base;branch=[]
    for s in cert['splits']:
        if s['y'] is None:continue
        val=dual(s['y'],(s['j'],s['value'])); assert val==F(s['L'])
        branch.append(val)
    if len(branch)==2:
        assert cert['splits'][0]['j']==cert['splits'][1]['j'] and cols[cert['splits'][0]['j']].is_binary()
        assert {s['value'] for s in cert['splits']}=={0,1}
        strongest=max(base,min(branch))
    assert strongest==F(summ['strongest_L'])
    start_counts=Counter()
    if cert['primal']:
        vals=list(map(F,cert['primal']));assert len(vals)==len(cols)
        for j,(v,z) in enumerate(zip(cols,vals)):
            assert (v.lb is None or numeric(v.lb)<=z) and (v.ub is None or numeric(v.ub)>=z)
            if v.is_binary(): assert z in (0,1)
            v.set_value(z,skip_validation=True)
        for row in rows:
            l,body,h=row.to_bounded_expression(evaluate_bounds=False);z=numeric(body)
            assert (l is None or numeric(l)<=z) and (h is None or numeric(h)>=z),row.name
        assert numeric(m.obj.expr)==F(summ['U'])
        for name,g in inp['thermal_generators'].items():
            prior=g['unit_on_t0'];down=g['time_down_t0'] if not prior else 0
            for t in range(1,T+1):
                on=int(numeric(m.ug[name,t]));v=int(numeric(m.vg[name,t]));w=int(numeric(m.wg[name,t]))
                ds=[j for j,_ in enumerate(g['startup']) if numeric(m.dg[name,j,t])]
                assert v==len(ds) and on-prior==v-w
                if not prior and on:
                    start_counts['true_starts']+=1
                    assert v==1 and len(ds)==1
                    chosen=ds[0]
                    eligible=[j for j,b in enumerate(g['startup']) if b['lag']<=down]
                    if eligible:
                        coldest=max(eligible,key=lambda j:g['startup'][j]['lag'])
                        if chosen==coldest:start_counts['category_matches_elapsed_offline']+=1
                        elif g['startup'][chosen]['cost']==g['startup'][coldest]['cost']:start_counts['different_label_equal_cost']+=1
                        elif g['startup'][chosen]['cost']>g['startup'][coldest]['cost']:start_counts['more_expensive_than_elapsed_category']+=1
                        else:start_counts['less_expensive_than_elapsed_category']+=1
                    else:start_counts['no_lag_eligible']+=1
                if v and prior==on:start_counts['simultaneous_marked_start_stop']+=1
                down=0 if on else down+1;prior=on
    return dict(input=p.name,T=T,exact_primal_official_rows=len(rows) if cert['primal'] else 0,
                zero_tol_primal=bool(cert['primal']),startup_history=dict(start_counts), independently_expanded_original_rows=len(rows),
                primal_U=summ['U'],exact_full_L=str(base),exact_combined_L=str(strongest),splits=len(branch))


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--source',type=Path,default=ROOT)
    parser.add_argument('--out',type=Path,required=True)
    opt=parser.parse_args();ROOT=opt.source.resolve();OUT=opt.out
    OUT.mkdir(parents=True,exist_ok=True)
    checks={'AC':[ac(p) for p in sorted((ROOT/'inputs').glob('*.m'))],
            'UC':[uc(p,t) for p in sorted((ROOT/'inputs').glob('20*.json')) for t in [24,48]]}
    (OUT/'receipt.json').write_text(json.dumps(checks,indent=2)+'\n')
    print('Rebuilt fresh AC and UC models,',sum(r['exact_primal_official_rows'] for r in checks['UC']),'UC primal row checks.')
