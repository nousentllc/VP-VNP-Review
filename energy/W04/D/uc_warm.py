"""W04-D. Four policies on one canonical Pyomo PGLib instance per timed run."""
import argparse, collections, gzip, json, os, resource, subprocess, sys, tempfile, time
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'foundation/src'))
import highspy as hs
import numpy as np
import pyomo.environ as pe
from scipy.sparse import csc_matrix,csr_matrix
from uc import build,truncate
from common import finite_bound

ARMS=['full','lp_start','group_start','permanent']
def write(path,data):
    tmp=path.with_suffix('.tmp')
    tmp.write_text(json.dumps(data,allow_nan=False,default=lambda x:x.item()))
    tmp.replace(path)

def worker(path,T,arm,out,share,effort):
    out.mkdir(parents=True,exist_ok=True)
    clock=time.monotonic
    start=clock()
    elapsed=lambda:clock()-start
    record=dict(case=path.stem,T=T,arm=arm,events=[],stages=[],start_monotonic=start)
    def checkpoint():write(out/'record.json',record)
    checkpoint()
    data=truncate(json.loads(path.read_text()),T)
    with tempfile.TemporaryDirectory() as tmp:
        inst=Path(tmp)/'case.json';inst.write_text(json.dumps(data))
        m,adapter,_=build(data,inst,'reference')
    solver=adapter._solver_model
    base=solver.getModel()
    lp=base.lp_; n=lp.num_col_;nr=lp.num_row_
    ix=adapter._pyomo_var_to_solver_var_map
    cols=np.empty(n,dtype=object)
    for v in m.component_data_objects(pe.Var):cols[ix[id(v)]]=v.name
    with gzip.open(out/'columns.json.gz','wt') as f:json.dump(cols.tolist(),f)
    M=lp.a_matrix_
    matrix_class=csc_matrix if M.format_==hs.MatrixFormat.kColwise else csr_matrix
    A=matrix_class((M.value_,M.index_,M.start_),shape=(nr,n))
    lo,hi,rl,rh,cost=map(np.asarray,(lp.col_lower_,lp.col_upper_,lp.row_lower_,lp.row_upper_,lp.col_cost_))
    integers=np.array([int(x)!=0 for x in lp.integrality_])
    gen=list(data['thermal_generators']);therm=data['thermal_generators']
    def ids(component,keys):
        return np.array([[ix[id(component[k,t])] for t in range(1,T+1)] for k in keys],dtype=int).reshape((-1,T))
    u,v,w,p,r=(ids(z,gen) for z in (m.ug,m.vg,m.wg,m.pg,m.rg))
    renewable=ids(m.pw,list(data['renewable_generators']))
    ini=np.array([therm[k]['unit_on_t0'] for k in gen])
    pmin=np.array([therm[k]['power_output_minimum'] for k in gen])
    record.update(build_s=elapsed(),shape=[nr,n],integers=int(sum(integers)),common_fallback=None)
    def residual(x):
        ax=A@x;du=np.diff(np.c_[ini,np.rint(x[u])],axis=1)
        balance=(x[p]+pmin[:,None]*x[u]).sum(0)+x[renewable].sum(0)-data['demand']
        return float(max(0.,np.max(rl-ax),np.max(ax-rh),np.max(lo-x),np.max(x-hi),
                   np.max(abs(x[integers]-np.rint(x[integers]))),np.max(abs(balance)),
                   np.max(np.asarray(data['reserves'])-x[r].sum(0)),np.max(abs(x[v]-np.maximum(0,du))),
                   np.max(abs(x[w]-np.maximum(0,-du)))))
    best=None;U=float('inf');L=None
    def accept(x,stage):
        nonlocal best,U
        obj=float(cost@x+lp.offset_)
        if obj>=U-1e-7:return
        t=elapsed();err=residual(x);validated=elapsed()
        if err>1e-4 or validated>45:
            record['events'].append(dict(stage=stage,t=validated,rejected=obj,residual=err));checkpoint();return
        filename=f'schedule_{len(record["events"])}.npz'
        np.savez_compressed(out/filename,x=x)
        best=x.copy();U=obj
        record['events'].append(dict(stage=stage,t=validated,U=obj,residual=err,validation_s=validated-t,file=filename))
        checkpoint()
    def lower(val,stage):
        nonlocal L
        z=finite_bound(val)
        if z is not None and elapsed()<=45 and (L is None or z>L+1e-6):
            L=z;record['events'].append(dict(stage=stage,t=elapsed(),L=z));checkpoint()
    def solve(h,stage,stop,full=False,relax=False,transfer=False):
        remaining=stop-elapsed()
        if remaining<=.03:
            record['stages'].append(dict(stage=stage,status='stage budget consumed'));checkpoint();return None
        s=dict(stage=stage,t_start=elapsed(),full=full,rows=h.getNumRow(),cols=h.getNumCol())
        record['stages'].append(s);checkpoint()
        for k,z in {'output_flag':True,'log_to_console':False,'log_file':str((out/(stage+'.log')).resolve()),
                    'threads':1,'mip_rel_gap':.005,'mip_feasibility_tolerance':1e-7,'random_seed':17,
                    'mip_heuristic_effort':effort,'presolve':'on'}.items():
            if h.setOptionValue(k,z)!=hs.HighsStatus.kOk:raise ValueError(k)
        if transfer and best is not None:
            t=elapsed()
            s['transfer_status']=str(h.setSolution(n,np.arange(n,dtype=np.int32),best));s['transfer_cost']=U
            s['transfer_s']=elapsed()-t
        def incumbent(ev):
            solution=np.asarray(ev.data_out.mip_solution)
            if solution.size==n:accept(solution,stage)
            if full:lower(ev.data_out.mip_dual_bound,stage)
        def tick(ev):
            if full:lower(ev.data_out.mip_dual_bound,stage)
            if elapsed()>stop:ev.interrupt()
        if not relax:h.cbMipImprovingSolution.subscribe(incumbent);h.cbMipInterrupt.subscribe(tick)
        h.setOptionValue('time_limit',max(.001,stop-elapsed()));h.run()
        sol=h.getSolution();s['status']=h.modelStatusToString(h.getModelStatus());s['return_s']=elapsed()
        info=h.getInfo()
        feasible=sol.value_valid and info.primal_solution_status==hs.kSolutionStatusFeasible
        if relax and feasible and s['status']=='Optimal':lower(h.getObjectiveValue()-1e-7*max(1,abs(h.getObjectiveValue())),stage)
        if not relax:
            s['stage_dual']=finite_bound(info.mip_dual_bound)
            if full:lower(info.mip_dual_bound,stage)
            if feasible:accept(np.asarray(sol.col_value),stage)
        s['start_log']=[line.strip() for line in (out/(stage+'.log')).read_text().splitlines()
                        if 'mip start' in line.lower() or 'user-supplied' in line.lower()]
        checkpoint()
        return np.array(sol.col_value) if feasible else None
    def fresh():
        h=hs.Highs();h.setOptionValue('output_flag',False);h.passModel(base);return h
    if arm=='full':solve(solver,'full',44.2,full=True)
    else:
        prep_end=45*share
        if arm in ('permanent','group_start'):
            groups=collections.defaultdict(list)
            for i,k in enumerate(gen):
                g=therm[k];groups[tuple(g[z] for z in ['unit_on_t0','time_up_minimum','time_down_minimum','must_run'])].append(i)
            pairs=[]
            for group in groups.values():
                group.sort(key=lambda i:(pmin[i],therm[gen[i]]['power_output_maximum'],gen[i]))
                pairs.extend(zip(group[::2],group[1::2]))
            ij=np.array([(u[i,h],u[j,h]) for i,j in pairs for h in range(T)],dtype=np.int32)
            q=len(ij);record['pairs']=len(pairs)
            solver.addRows(q,np.zeros(q),np.zeros(q),2*q,np.arange(0,2*q+1,2,dtype=np.int32),ij.ravel(),np.tile([1.,-1.],q))
            solve(solver,'paired',44.2 if arm=='permanent' else prep_end)
        else:
            indices=np.flatnonzero(integers).astype(np.int32)
            solver.changeColsIntegrality(len(indices),indices,np.zeros(len(indices),dtype=np.uint8))
            x=solve(solver,'outer_lp',prep_end,relax=True)
            if x is not None and elapsed()<prep_end:
                repair=fresh()
                # Fix high-confidence commitment decisions only; all other binaries remain integral.
                ui=u.ravel();sel=ui[(x[ui]<=.10)|(x[ui]>=.90)].astype(np.int32)
                z=np.rint(x[sel]);repair.changeColsBounds(len(sel),sel,z,z)
                record['rounded_commitments']=len(sel);solve(repair,'sign_repair',prep_end)
        if arm!='permanent':
            full=fresh()
            if full.getNumRow()!=nr or sum(int(z)!=0 for z in full.getLp().integrality_)!=sum(integers):
                raise ValueError('Recovery failed to restore original model')
            solve(full,'recovered_full',44.2,full=True,transfer=True)
    record.update(done=True,elapsed=elapsed(),peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    checkpoint()

def launch(path,T,arm,out,share,effort):
    dest=out/f'{path.stem}_{T}_{arm}';dest.mkdir(parents=True,exist_ok=True)
    if (dest/'supervisor.json').exists():raise ValueError('Choose a fresh output directory')
    args=[sys.executable,__file__,'worker',str(path),str(T),arm,str(dest),str(share),str(effort)]
    with (dest/'console.log').open('w') as f:
        child=subprocess.Popen(args,stdout=f,stderr=f)
        launched=time.monotonic();start=None;killed=False
        while child.poll() is None:
            if start is None and (dest/'record.json').exists():start=json.loads((dest/'record.json').read_text())['start_monotonic']
            if time.monotonic()>(start+45.25 if start else launched+15):
                child.kill();child.wait();killed=True;break
            time.sleep(.03)
    write(dest/'supervisor.json',dict(exit=child.returncode,killed=killed,total_wall_s=time.monotonic()-launched))
    return dest

if __name__=='__main__':
    import sys
    if sys.argv[1]=='worker':
        _,_,f,t,a,o,s,e=sys.argv;worker(Path(f),int(t),a,Path(o),float(s),float(e))
    elif sys.argv[1]=='develop':
        out=Path(sys.argv[2]);f=HERE.parent/'foundation/inputs/uc/rts_2020-03-05.json'
        for a,share,eff in [('full',.3,.05),('full',.3,.15),('lp_start',.3,.05),('group_start',.3,.05)]:
            launch(f,12,a,out/str(eff),share,eff)
    elif sys.argv[1]=='run':
        out=Path(sys.argv[2]);lock=json.loads((HERE/'freeze.json').read_text())
        for j,f in enumerate(sorted((HERE/'inputs').glob('*.json'))):
            for k,T in enumerate([12,48]):
                order=(j+k)%4
                for arm in ARMS[order:]+ARMS[:order]:
                    d=launch(f,T,arm,out,lock['candidate_share'],lock['effort'])
                    print(d.name,flush=True)
