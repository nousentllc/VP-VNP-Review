"""PGLib-UC reference formulation with a paired-commitment inner restriction."""
import contextlib
import gc
import io
import json
import sys
import tempfile
import time
from collections import defaultdict
from pathlib import Path
import highspy as hs
import numpy as np
import pyomo.environ as pe
from pyomo.contrib.appsi.solvers.highs import Highs
from common import ROOT,OUT,DESIGN,save,finite_bound

CFG=DESIGN['D']


def truncate(data,t):
    if t>data['time_periods']:raise ValueError(t)
    data['time_periods']=t
    for k in ['reserves','demand']:data[k]=data[k][:t]
    for w in data['renewable_generators'].values():
        for k in ['power_output_minimum','power_output_maximum']:w[k]=w[k][:t]
    return data


def build(data,instance,policy):
    ref=(ROOT/'inputs/uc/uc_model.py').read_text().split('print("model setup complete")')[0]
    old=sys.argv
    try:
        sys.argv=['uc_model.py',str(instance)]
        scope={}
        with contextlib.redirect_stdout(io.StringIO()):
            exec(compile(ref,'pinned_pglib_uc_model.py','exec'),scope)
    finally: sys.argv=old
    m=scope['m']
    pairs=[]
    if policy=='paired_commitment':
        subsets=defaultdict(list);gens=data['thermal_generators']
        for key,g in gens.items():
            category=tuple(g[x] for x in ['unit_on_t0','time_up_minimum','time_down_minimum','must_run'])
            subsets[category].append(key)
        m.shared_commitment=pe.ConstraintList()
        for group in subsets.values():
            group.sort(key=lambda k:(gens[k]['power_output_minimum'],gens[k]['power_output_maximum'],k))
            for i,j in zip(group[::2],group[1::2]):
                pairs.append([i,j])
                for t in range(1,data['time_periods']+1):
                    m.shared_commitment.add(m.ug[i,t]==m.ug[j,t])
    adapter=Highs()
    adapter.set_instance(m)
    return m,adapter,pairs


def physical(data,m):
    gen=data['thermal_generators']; periods=list(range(1,data['time_periods']+1))
    power=np.zeros(len(periods));reserve=power.copy()
    violations=defaultdict(float);starts=0;num_on=0
    def exceed(key,*vals):violations[key]=max(violations[key],*vals)
    for name,g in gen.items():
        before=g['unit_on_t0']; age=g['time_up_t0'] if before else g['time_down_t0']
        pprev=before*(g['power_output_t0']-g['power_output_minimum'])
        for ix,t in enumerate(periods):
            u=round(m.ug[name,t].value); v=round(m.vg[name,t].value); w=round(m.wg[name,t].value)
            p=m.pg[name,t].value; r=m.rg[name,t].value
            power[ix]+=p+u*g['power_output_minimum'];reserve[ix]+=r;starts+=v;num_on+=u
            exceed('start_stop',abs(v-max(0,u-before)),abs(w-max(0,before-u)))
            if u!=before:
                required=g['time_up_minimum'] if before else g['time_down_minimum']
                exceed('minimum_duration',required-age)
                age=0
            nameplate=g['power_output_maximum']-g['power_output_minimum']
            exceed('output_headroom',p+r-u*nameplate,-p,-r,g['must_run']-u)
            exceed('ramp',p+r-pprev-g['ramp_up_limit'],pprev-p-g['ramp_down_limit'])
            if v:exceed('startup_cap',p+r+g['power_output_minimum']-g['ramp_startup_limit'])
            if w:exceed('shutdown_cap',pprev+g['power_output_minimum']-g['ramp_shutdown_limit'])
            before=u;age+=1;pprev=p
    for name,renew in data['renewable_generators'].items():
        p=np.array([m.pw[name,h].value for h in periods]);power+=p
        exceed('renewable',max(p-renew['power_output_maximum']),max(renew['power_output_minimum']-p))
    exceed('balance',max(abs(power-np.asarray(data['demand']))))
    exceed('reserve',max(np.asarray(data['reserves'])-reserve))
    return dict(max_violations=dict(violations),starts=starts,on_unit_hours=num_on,
                reserve_MW=reserve.tolist(),supplied_MW=power.tolist())


def validate(data,m):
    max_row=max_box=max_int=0.
    for row in m.component_data_objects(pe.Constraint,active=True):
        x=pe.value(row.body)
        if row.lower is not None:max_row=max(max_row,pe.value(row.lower)-x)
        if row.upper is not None:max_row=max(max_row,x-pe.value(row.upper))
    for v in m.component_data_objects(pe.Var,active=True):
        x=v.value
        if x is None:raise ValueError(v.name+' missing')
        if v.lb is not None:max_box=max(max_box,v.lb-x)
        if v.ub is not None:max_box=max(max_box,x-v.ub)
        if v.is_integer():max_int=max(max_int,abs(x-round(x)))
    replay=physical(data,m)
    valid=max(max_row,max_box,max_int,*replay['max_violations'].values())<=CFG['tolerance']
    return dict(valid=valid,canonical_row_violation=max_row,box_violation=max_box,
                integrality=max_int,objective=pe.value(m.obj),**replay)


def trial(path,horizon,policy,out):
    start=time.perf_counter(); now=lambda:time.perf_counter()-start
    data=truncate(json.loads(path.read_text()),horizon)
    rid=f'{path.stem}_{horizon}h_{policy}'
    record=dict(id=rid,instance=path.stem,hours=horizon,generators=len(data['thermal_generators']),
                policy=policy,trace=[],validated_by_deadline=False)
    with tempfile.TemporaryDirectory() as tmp:
        inst=Path(tmp)/'instance.json';inst.write_text(json.dumps(data))
        m,adapter,pairs=build(data,inst,policy)
    h=adapter._solver_model
    for k,v in {'threads':1,'random_seed':17,'mip_rel_gap':CFG['solver_mip_rel_gap'],
                'output_flag':False,'presolve':'on','mip_feasibility_tolerance':1e-7}.items():
        h.setOptionValue(k,v)
    record.update(pairs=pairs,build_seconds=now(),rows=h.getNumRow(),columns=h.getNumCol())
    # Checking the largest schedules is material. Reserve the same 20% wall budget in each arm.
    remaining=CFG['seconds_per_policy']*.80-now()
    if remaining<=0:
        record.update(status='construction_used_solver_budget',elapsed=now())
        return record
    h.setOptionValue('time_limit',remaining)
    def event(ev):
        ub,lb=finite_bound(ev.data_out.mip_primal_bound),finite_bound(ev.data_out.mip_dual_bound)
        last=record['trace'][-1] if record['trace'] else {}
        if (ub,lb)!=(last.get('U'),last.get('L')):
            record['trace'].append(dict(time=now(),U=ub,L=lb))
    h.cbMipInterrupt.subscribe(event);h.cbMipImprovingSolution.subscribe(event)
    h.run()
    sol=h.getSolution();info=h.getInfo()
    record.update(status=h.modelStatusToString(h.getModelStatus()),solver_return=now(),nodes=info.mip_node_count,
                  solver_dual=finite_bound(info.mip_dual_bound),
                  bound_scope='unrestricted PGLib UC' if policy=='reference' else 'paired restriction only')
    if sol.value_valid and info.primal_solution_status==hs.kSolutionStatusFeasible:
        candidate=np.asarray(sol.col_value)
        chosen=list(m.component_data_objects(pe.Var,active=True))
        index=adapter._pyomo_var_to_solver_var_map
        values=np.asarray([candidate[index[id(v)]] for v in chosen])
        for v,value in zip(chosen,values):v.set_value(float(value),skip_validation=True)
        check=validate(data,m)
        record.update(check=check,validated_by_deadline=check['valid'] and now()<=CFG['seconds_per_policy'],
                      validation_seconds=now()-record['solver_return'])
        record['schedule_file']=rid+'.npz'
        np.savez_compressed(out/record['schedule_file'],values=values,
                            names=np.array([v.name for v in chosen]))
    record['elapsed']=now()
    return record


def run():
    out=OUT/'D';out.mkdir(exist_ok=True)
    for index,name in enumerate(CFG['instances']):
        for j,hor in enumerate(CFG['horizons']):
            policies=CFG['policies'] if (index+j)%2==0 else CFG['policies'][::-1]
            for policy in policies:
                rec=trial(ROOT/'inputs/uc'/(name+'.json'),hor,policy,out)
                save(out/(rec['id']+'.json'),rec)
                print(rec['id'],rec['status'],rec['validated_by_deadline'],flush=True)
                gc.collect()


if __name__=='__main__':run()
