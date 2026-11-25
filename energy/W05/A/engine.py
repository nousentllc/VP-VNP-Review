"""W05 certified LP screening. All accepted powers are checked on individual devices."""
import hashlib
import json
import math
import os
import resource
import sys
import tempfile
import time
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
W04 = HERE.parents[1] / 'W04'
FOUND = W04 / 'foundation'
os.environ.setdefault('W03_RESULTS', str(Path(tempfile.gettempdir())/'w05a_model_cache'))
sys.path.insert(0,str(FOUND/'src'))
from battery_inputs import make_case
from battery_model import arrays, model, validate
from battery_audit import exact_box, direct
from common import finite_bound
import highspy as hs
import numpy as np

ARMS = ['native_cert','lp_only','lp_repair','screen','native_unmetered_certificate']
SEEDS = [11903,11927,11939,11953]
FAMILIES = ['ordinary','negative_outage','forced_opposition','tight_reserve','unknown_exchange']
SIZES = [(4,8),(12,16),(20,24)]
CLOCKS = [.05,.1,.25,.5,1.,2.]
BUDGET = 2.0
def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def records():
    """No solver calls. Fallback powers absent (not just masked) in unavailable cases."""
    out=[]
    for n,t in SIZES:
        for i,seed in enumerate(SEEDS):
            for j,name in enumerate(FAMILIES):
                origin=name if name in ('ordinary','negative_outage','forced_opposition') else 'negative_outage'
                a=make_case(seed+37*j,n,t,origin)
                a['generator_seed']=seed+37*j
                a['seed']=seed;a['cohort']=name;a['id']=f'{name}_{n}x{t}_{seed}'
                supplied=i%2==0 and name!='unknown_exchange'
                if name=='tight_reserve':
                    a['price'][1::4]=-37.; a['eta_d']=np.linspace(.73,.98,n)
                    a['eta_c']=np.linspace(.97,.76,n)
                    a['floor'][:]=a['initial'][:,None]*.975
                    a['ramp']=.12*n
                    a['load'][:]=1.15*n+.035*n*np.sin(np.arange(t)*.7)
                    a['previous']=float(a['load'][0]);a['grid_hi']=a['load']+.06*n
                    a['terminal_tolerance'][:]=.001
                if name=='unknown_exchange':
                    # No feasible plan used in generation; new exogenous target and reserve availability shock.
                    a['eta_c']=np.linspace(.77,.98,n);a['eta_d']=np.linspace(.96,.78,n)
                    a['availability'][::2,t//3:t//3+2]=0.
                    a['floor'][:,t//2:]=a['initial'][:,None]*(.87+.03*(i%3))
                    a['ramp']=.25*n
                    a['load'][:]=1.1*n+.026*n*np.cos(np.arange(t)*1.2)
                    mid=1.1*n+.085*n*np.sin(np.arange(t)*np.pi/3)
                    a['previous']=float(mid[0]);a['grid_lo']=mid-.012*n;a['grid_hi']=mid+.012*n
                    a['terminal_tolerance'][:]=.001
                if name in ('ordinary','negative_outage') and i%2:a['terminal_tolerance']=.02*a['capacity']
                a['fallback_supplied']=supplied
                if not supplied:
                    a.pop('fallback_charge');a.pop('fallback_discharge')
                out.append({k:v.tolist() if isinstance(v,np.ndarray) else v for k,v in a.items()})
    return out

def vector(a,c,d):
    e=a['initial'][:,None]+np.cumsum(a['eta_c'][:,None]*c-d/a['eta_d'][:,None],axis=1)
    g=a['load']+(c-d).sum(axis=0)
    return np.r_[c.ravel(),d.ravel(),e.ravel(),g,(c>d).astype(float).ravel()]

def round_lower(value):
    el=float(value)
    return math.nextafter(el,-math.inf) if Fraction.from_float(el)>value else el

def run_trial(record,arm,rep,tuning):
    start=time.monotonic_ns()
    elapsed=lambda:(time.monotonic_ns()-start)*1e-9
    a=arrays(record)
    n,t=a['n'],a['t'];units=[[i] for i in range(n)]
    row=dict(case=a['id'],seed=a['seed'],arm=arm,repeat=rep,cohort=a['cohort'],size=[n,t],
             supplied=bool(a['fallback_supplied']),events=[],witnesses=[],certificates=[],stages=[],target=None)
    best=math.inf;bound=-math.inf;inc=None;source=None;fallback=None
    def check_gap(ts):
        if row['target'] is None and ts<=BUDGET and math.isfinite(best) and math.isfinite(bound):
            if best<bound-2e-5:raise ValueError(('upper below lower',best,bound))
            if best-bound<=2e-5+.001*max(1,abs(best)):row['target']=ts
    def offer(c,d,tag,stage=None,record_all=False):
        nonlocal best,inc,source
        at=elapsed();result=validate(a,c,d);ts=elapsed()
        if stage is not None:stage['validation_s']+=ts-at
        improves=result['valid'] and ts<=BUDGET and result['cost']<best-1e-8
        if improves or record_all:
            wi=len(row['witnesses']);row['witnesses'].append(dict(id=wi,stage=tag,at=ts,**result,c=c.tolist(),d=d.tolist()))
            if improves:
                best=result['cost'];inc=(c.copy(),d.copy());source=tag
                row['events'].append(dict(at=ts,U=best,witness=wi,stage=tag));check_gap(ts)
        return result
    if a['fallback_supplied']:
        w=offer(a['fallback_charge'],a['fallback_discharge'],'fallback',record_all=True)
        if not w['valid']:raise ValueError('Supplied invalid fallback.')
        fallback=w['cost']
    def solve(label,end,kind='mixed',fixed=None,partial=None,use_lp_candidate=True):
        nonlocal bound
        b0=elapsed()
        if b0>=end:
            row['stages'].append(dict(label=label,status='not_started_time_gate',start=b0));return None
        m,ic,idd=model(a,units,kind,fixed)
        if partial is not None:
            k=len(m.lo)-n*t
            for j,z in enumerate(partial.ravel()):
                if z>=0:m.lo[k+j]=m.hi[k+j]=int(z)
        integer=any(m.integer)
        h=m.solver('on',1e-6)
        if h.setOptionValue('mip_heuristic_effort',tuning['effort'])!=hs.HighsStatus.kOk:
            raise ValueError('Solver effort setting rejected.')
        s=dict(label=label,start=b0,build_s=elapsed()-b0,validation_s=0.,solver='mip' if integer else 'lp',
               num_rows=len(m.lhs),num_cols=len(m.lo),integers=int(sum(m.integer)),transfer_s=0.)
        row['stages'].append(s)
        tmp=tempfile.TemporaryDirectory()
        log=Path(tmp.name)/'highs.log'
        h.setOptionValue('log_file',str(log));h.setOptionValue('log_to_console',False);h.setOptionValue('output_flag',True)
        if integer and inc is not None:
            t0=elapsed();x=vector(a,*inc);ax=m.A@x
            err=max(0.,max(np.array(m.lo)-x),max(x-np.array(m.hi)),max(np.array(m.lhs)-ax),max(ax-np.array(m.rhs)))
            s.update(transfer_source=source,transfer_matrix_violation=float(err),transfer_cost=best)
            if err<=2e-6:s['transfer_api']=str(h.setSolution(len(x),np.arange(len(x),dtype=np.int32),x))
            s['transfer_s']=elapsed()-t0
        def cb(ev):
            if elapsed()>=end:ev.interrupt()
        def improve(ev):
            x=np.asarray(ev.data_out.mip_solution)
            if len(x)==len(m.lo):offer(x[ic],x[idd],label,s)
        if integer:
            h.cbMipInterrupt.subscribe(cb);h.cbMipImprovingSolution.subscribe(improve)
        if elapsed()>=end:
            s.update(status='build_exhausted',end=elapsed());tmp.cleanup();return None
        h.setOptionValue('time_limit',max(1e-6,end-elapsed()))
        t0=elapsed();ret=h.run();s['solve_with_callbacks_s']=elapsed()-t0
        sol=h.getSolution();info=h.getInfo();s.update(status=h.modelStatusToString(h.getModelStatus()),solver_api=str(ret),
            nodes=int(info.mip_node_count) if integer else None,lp_iterations=int(info.simplex_iteration_count))
        s['return_time']=elapsed()
        if integer and label=='native':
            s['numerical_native_lower']=finite_bound(info.mip_dual_bound)
        powers=None
        if sol.value_valid and info.primal_solution_status==hs.kSolutionStatusFeasible:
            x=np.asarray(sol.col_value);powers=(x[ic],x[idd])
            if kind!='lp' or use_lp_candidate:offer(*powers,label,s,True)
        if label in ('outer_lp','certificate_lp') and sol.dual_valid:
            t0=elapsed();dual=sol.row_dual
            exact=exact_box(m,dual);lo=round_lower(exact);ts=elapsed()
            s['certificate_s']=ts-t0;s['certificate_ready']=ts
            row['certificates'].append(dict(stage=label,at=ts,lower=lo,fraction=str(exact),dual=dual))
            if ts<=BUDGET and lo>bound:
                bound=lo;row['events'].append(dict(at=ts,L=lo,stage=label));check_gap(ts)
        h.setOptionValue('log_file','')
        s['log']=log.read_text() if log.exists() else ''
        s['confirmed_start']=('mip start solution is feasible' in s['log'].lower())
        s['end']=elapsed();tmp.cleanup();return powers
    if arm in ('native_cert','native_unmetered_certificate'):
        # Native reference starts with the MIP; either reserve part of the two seconds
        # for an independent bound, or give it the entire budget as a diagnostic.
        end=BUDGET*(1-tuning['reserve']) if arm=='native_cert' else BUDGET
        solve('native',end)
        if arm=='native_cert':solve('certificate_lp',BUDGET,'lp',use_lp_candidate=False)
    else:
        powers=solve('outer_lp',BUDGET,'lp')
        if arm!='lp_only' and row['target'] is None:
            if arm=='lp_repair' and powers is not None:
                c,d=powers;end=BUDGET*tuning['repair_share']
                solve('fixed_sign',end,fixed=(c>=d).astype(float))
                if row['target'] is None:
                    sure=np.where((c>2e-6)&(d<=2e-6),1.,np.where((d>2e-6)&(c<=2e-6),0.,-1.))
                    solve('partial_sign',end,partial=sure)
            if row['target'] is None:solve('native',BUDGET)
    row.update(wall=elapsed(),fallback_cost=fallback,
               peak_rss_native_units=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return row
