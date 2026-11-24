"""Post-run exact lower bounds on the binary64 LP instances and schedule replay."""
import gzip
import json
import time
from fractions import Fraction as F
import numpy as np
from common import ROOT,OUT,save
from battery_model import arrays,model


def direct(a,powers):
    c,d=np.asarray(powers,dtype=float)
    e=a['initial'].copy();gprev=a['previous'];cost=worst=0.
    for t in range(a['t']):
        g=a['load'][t]
        for i in range(a['n']):
            ch,dis=c[i,t],d[i,t]
            lim=a['power'][i]*a['availability'][i,t]
            e[i]+=a['eta_c'][i]*ch-dis/a['eta_d'][i]
            g+=ch-dis
            worst=max(worst,-ch,-dis,ch-lim,dis-lim,min(ch,dis),a['floor'][i,t]-e[i],e[i]-a['capacity'][i])
            cost+=(ch+dis)*a['wear'][i]
        worst=max(worst,a['grid_lo'][t]-g,g-a['grid_hi'][t],abs(g-gprev)-a['ramp'])
        cost+=g*a['price'][t];gprev=g
    worst=max(worst,max(abs(e-a['initial'])-a['terminal_tolerance']))
    return float(cost),float(worst)


def exact_box(m,dual):
    zero=F(0); total=zero
    residual=[F.from_float(float(v)) for v in m.cost]
    ys=[]
    for val,lo,hi in zip(dual,m.lhs,m.rhs):
        y=F.from_float(float(val))
        side=lo if y>0 else hi
        if not np.isfinite(side):y=zero
        if y:total+=y*F.from_float(float(side))
        ys.append(y)
    for row,col,v in zip(m.row,m.col,m.val):
        if ys[row]:residual[col]-=ys[row]*F.from_float(float(v))
    for co,lo,hi in zip(residual,m.lo,m.hi):
        if co:total+=co*F.from_float(float(lo if co>0 else hi))
    return total


def run():
    cases=[arrays(v) for v in json.loads((ROOT/'inputs/battery_holdout.json').read_text())]
    index={a['id']:a for a in cases}
    rows=[json.loads(v) for v in gzip.open(OUT/'A/holdout.jsonl.gz','rt')]
    replays=0;disagreed=0;worst=0.
    for row in rows:
        if row['repeat']!=0:continue
        a=index[row['case']];cost,err=direct(a,row['best_powers'])
        if err>2e-6 or abs(cost-row['upper'])>1e-5:raise ValueError(row['case'])
        replays+=1
        for step in row['steps']:
            if 'returned_powers' not in step:continue
            cost,err=direct(a,step['returned_powers'])
            check=step['returned_check']
            if bool(err<=2e-6)!=bool(check['valid']) or abs(cost-check['cost'])>1e-5:disagreed+=1
            replays+=1
            if check['valid']:worst=max(worst,err)
    certificates=[];reductions=[]
    for a in cases:
        ids=[[i] for i in range(a['n'])];half=a['n']//2
        for label,groups,kind in [('full_lp',ids,'lp'),('full_milp',ids,'mixed'),
                                   ('root_shared',[sum(ids,[])],'mixed'),
                                   ('fixed_shared',[list(range(half)),list(range(half,a['n']))],'mixed'),
                                   ('fixed_proportional',[list(range(half)),list(range(half,a['n']))],'proportional')]:
            m,_,_=model(a,groups,kind)
            h=m.solver('on',1e-6);stamp=time.perf_counter();h.presolve()
            duration=time.perf_counter()-stamp;p=h.getPresolvedLp()
            reductions.append(dict(case=a['id'],form=label,presolve_seconds=duration,
                                   status=str(h.getModelPresolveStatus()),original=[h.getNumRow(),h.getNumCol(),h.getNumNz()],
                                   reduced=[p.num_row_,p.num_col_,len(p.a_matrix_.value_)]))
            if label=='full_lp':
                h.run();y=h.getSolution().row_dual
                bound=exact_box(m,y)
                admissible=[r['upper'] for r in rows if r['case']==a['id']]
                if float(bound)>min(admissible)+1e-5:raise ValueError(a['id'])
                certificates.append(dict(case=a['id'],exact_lower=str(bound),lower=float(bound),
                                         lp_objective=h.getObjectiveValue(),row_dual=y))
    if disagreed:raise ValueError(disagreed)
    save(OUT/'A/exact_lp_certificates.json',certificates)
    save(OUT/'A/presolve_diagnostics.json',reductions)
    save(OUT/'A/independent_replay.json',dict(replays=replays,classification_disagreements=disagreed,
                                              max_residual_valid_returns=worst))


if __name__=='__main__':run()
