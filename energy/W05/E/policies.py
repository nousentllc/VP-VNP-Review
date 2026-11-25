"""Causal dispatch with original W04 storage dynamics and lexicographic LPs."""
import gzip
import hashlib
import json
import os
import sys
import time
from pathlib import Path

for name in ("OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS","VECLIB_MAXIMUM_THREADS"):
    os.environ[name]="1"
ROOT=Path(__file__).resolve().parent
W04=Path(os.environ.get("W05_W04_ROOT",ROOT.parent.parent/"W04")).resolve()
sys.path.insert(0,str(W04/"E"))
import campaign as old
import numpy as np
import highspy
from scipy.sparse import csr_matrix

P=old.P
HORIZONS=(3,6,12)
RULES=("original","scaled2","fill")
ARMS=[f"{name}{h}" for h in HORIZONS for name in ("rule","none","w04","learned")]+[
    "legacyrule6","legacyrule12","nestedrule6","nested6","adaptive","fixed12","flat12","offline"]
TOL=1e-6

def clean(x):
    if isinstance(x,np.ndarray):return x.tolist()
    if isinstance(x,np.generic):return x.item()
    raise TypeError(type(x).__name__)

def dump(path,obj):
    path=Path(path);path.parent.mkdir(exist_ok=True,parents=True)
    b=json.dumps(obj,default=clean,separators=(",",":"),sort_keys=True,allow_nan=False).encode()
    path.write_bytes(gzip.compress(b,compresslevel=6,mtime=0) if path.suffix==".gz" else b)

def read(path):
    path=Path(path)
    return json.loads(gzip.decompress(path.read_bytes()) if path.suffix==".gz" else path.read_bytes())

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def rule(fc,avail,floors,reserve,e,prev,name):
    if name=="original":return old.old.rule(fc,avail,floors,reserve,e,prev)
    if name not in RULES:raise ValueError(name)
    cap=min(P['grid_cap'],prev+P['ramp'])
    obligation=max(0.,(floors[0]-e)/P['eta_c'])
    target=P['energy'] if name=='fill' else min(P['energy'],max(P['initial'],max(floors)+2*sum(max(0.,x-P['grid_cap']) for x in fc[1:])/P['eta_d']))
    discharge=min(max(0.,P['power']*avail[0]-reserve[0]),max(0.,fc[0]-cap),max(0.,e-floors[0])*P['eta_d'])
    charge=0. if discharge>1e-10 else min(P['power']*avail[0],(P['energy']-e)/P['eta_c'],
                    max(obligation,min(max(0.,cap-fc[0]),max(0.,target-e)/P['eta_c'])))
    grid=min(cap,fc[0]+charge-discharge)
    return np.array([grid,charge,discharge,max(0.,fc[0]-grid+charge-discharge),e+P['eta_c']*charge-discharge/P['eta_d']])

def lex(fc,avail,floors,reserve,e,prev,target=None):
    ids,eq,rhs,ineq,ranges,box=old.matrix(fc,avail,floors,reserve,e,prev)
    mat=csr_matrix(np.vstack([eq,ineq]))
    model=highspy.Highs()
    for key,value in [('output_flag',False),('threads',1),('solver','simplex'),('presolve','on'),
                      ('primal_feasibility_tolerance',1e-8),('dual_feasibility_tolerance',1e-8),('random_seed',1705)]:
        if model.setOptionValue(key,value)!=highspy.HighsStatus.kOk:raise ValueError(key)
    box=np.asarray(box);n=len(box);indices=np.arange(n,dtype=np.int32)
    model.addVars(n,box[:,0],box[:,1])
    model.addRows(mat.shape[0],np.r_[rhs,np.full(len(ranges),-highspy.kHighsInf)],np.r_[rhs,ranges],
                  mat.nnz,mat.indptr,mat.indices,mat.data)
    stages={}
    def solve(ix,sense,name,fix=True):
        ix=np.asarray(ix,dtype=np.int32).ravel();obj=np.zeros(n);obj[ix]=sense
        model.changeColsCost(n,indices,obj)
        model.run();stat=model.getModelStatus()
        if stat!=highspy.HighsModelStatus.kOptimal:raise RuntimeError(name+" "+str(stat))
        val=model.getObjectiveValue();stages[name]=val
        if fix:model.addRow(val,val,len(ix),ix,np.full(len(ix),float(sense)))
        return np.array(model.getSolution().col_value).reshape(-1,5)
    solve(ids[:,3],1,'shed')
    if target is not None and target>floors[-1]+1e-8:
        x=solve([ids[-1,4]],-1,'negative_max_soc',False)
        model.changeColBounds(int(ids[-1,4]),max(floors[-1],min(target,x[-1,4])),P['energy'])
    solve(ids[:,1:3],1,'throughput')
    solve([ids[0,3]],1,'first_shed')
    solve([ids[0,1]],1,'first_charge')
    x=solve([ids[0,2]],1,'first_discharge',False)
    return x,stages

def fit(cases):
    """Nonparametric tail target on W04 data. Same day is not repeated across regimes."""
    xs=[];needs=[]
    for case in cases:
        if case['regime']!='base':continue
        load=np.array(case['load'])
        for boundary in range(23):
            future=load[boundary+1:boundary+9]
            net=np.clip(future-P['grid_cap'],-P['power'],P['power'])
            draw=np.where(net>0,net/P['eta_d'],net*P['eta_c'])
            xs.append([boundary/3.0,load[boundary]/12.])
            needs.append(max(0.,max(np.cumsum(draw))))
    return dict(xs=xs,needs=needs,neighbors=48,quantile=.90,tail_hours=8)

def target_at(kind,idx,fc,fs,config):
    if kind=='none':return None
    if idx[-1]==23:return fs[-1]
    if kind=='w04':extra=config['old_extra'][idx[-1]//4]
    else:
        d=config['learned'];x=np.asarray(d['xs']);dist=(x[:,0]-idx[-1]/3.)**2+(x[:,1]-fc[-1]/12.)**2
        # Stable ordering preserves training enumeration across tied distances.
        chosen=np.argsort(dist,kind='stable')[:d['neighbors']]
        extra=np.quantile(np.asarray(d['needs'])[chosen],d['quantile'])
    return min(P['energy'],fs[-1]+extra)

def policy(c,arm,config,override_rule=None,clock_signals=None):
    e=P['initial'];prev=P['previous'];arr=[];dec=[]
    floors=np.array(c['floor']);reserve=np.array(c['reserve'])
    avail=np.array(c['available']);load=np.array(c['load'])
    offsec=None
    if arm=="offline":
        tic=time.perf_counter();plan,status=old.old.lp(load,avail,floors,reserve,e,prev)
        offsec=time.perf_counter()-tic
        if plan is None:raise RuntimeError(status)
    for t,issue in enumerate(c['issues']):
        tic=time.perf_counter()
        primary_h=int(arm[3:]) if arm.startswith('w04') else int(''.join(i for i in arm if i.isdigit()) or '12')
        info_h=12 if arm in ('nested6','nestedrule6','adaptive','fixed12','flat12','offline') else primary_h
        idx=np.asarray(issue['valid'][:info_h]);fc=np.array(issue['load'][:info_h]);av=np.array(issue['available'][:info_h])
        if fc[0]!=load[t] or av[0]!=avail[t]:raise ValueError("issue")
        rs=reserve[idx];fs=floors[idx]
        safe=rule(fc[:1],av[:1],fs[:1],rs[:1],e,prev,"original")
        safe_err=old.old.check(safe,e,prev,load[t],avail[t],floors[t],reserve[t])
        if safe_err>TOL:raise RuntimeError(f"no valid common fallback {safe_err}")
        safe_sec=time.perf_counter()-tic;used=len(idx);goal=None;stages={};failure=None;calls=[]
        def candidate(h,kind,local_fc):
            nonlocal goal
            goal=target_at(kind,idx[:h],local_fc[:h],fs[:h],config)
            path,values=lex(local_fc[:h],av[:h],fs[:h],rs[:h],e,prev,goal)
            calls.append(dict(h=len(path),target=goal,stage=values))
            return path[0],goal,values
        try:
            if arm=='offline':act=plan[t]
            elif arm.startswith('legacyrule'):
                act=rule(fc,av,fs,rs,e,prev,'original')
            elif arm=='nestedrule6':
                used=min(6,len(fc));act=rule(fc[:used],av[:used],fs[:used],rs[:used],e,prev,config['rules']['6'])
            elif arm.startswith("rule"):
                act=rule(fc,av,fs,rs,e,prev,override_rule or config['rules'][str(primary_h)])
            elif arm in ('adaptive','fixed12'):
                short=candidate(6,'learned',fc)
                long=candidate(12,'learned',fc)
                # Uses issued forecast, never realized future. Both policies buy both solves.
                choose_short=(arm=='adaptive' and len(fc)>6 and np.mean(fc[6:])-np.mean(fc[:6])<config['switch_tail_difference'])
                act,goal,stages=short if choose_short else long
                used=min(len(idx),6 if choose_short else 12)
            else:
                kind='w04' if arm.startswith('w04') else 'none' if arm.startswith('none') else 'learned'
                used=min(6,len(idx)) if arm=="nested6" else len(idx)
                eff=fc.copy()
                if arm=='flat12' and len(eff)>6:eff[6:]=eff[5]
                act,goal,stages=candidate(used,kind,eff)
            err=old.old.check(act,e,prev,load[t],avail[t],floors[t],reserve[t])
            if err>TOL or not np.isfinite(act).all():raise RuntimeError(f"candidate check {err}")
        except RuntimeError as exc:
            if arm=='offline':raise
            failure=str(exc);act=safe
        elapsed=time.perf_counter()-tic
        deadline=clock_signals[t] if clock_signals is not None else elapsed>P['online_deadline']
        if arm!='offline' and deadline:
            failure=(failure+' + ' if failure else '')+'deadline'
            act=safe
        arr.append(act.tolist());dec.append(dict(h=t,info=len(idx),used=used,target=goal,calls=calls,
             reason=failure,safe_seconds=safe_sec,ready_seconds=elapsed,clock_fallback=bool(deadline) if arm!='offline' else False))
        prev,e=act[0],act[4]
    return dict(case=c['id'],seed=c['seed'],regime=c['regime'],panel=c.get('panel','development'),arm=arm,
                actions=arr,decisions=dec,offline_seconds=offsec)
