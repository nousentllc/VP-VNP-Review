import sys,resource,json,time,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'foundation/src'))
from ac import read_case,starts,independent,dispatch_floor,ca,np,save,CFG
from structure import probe
def solve(path,policy,rep,opts,out):
    start=time.perf_counter()
    a=read_case(path)
    bus,g,br,b,coef=a['bus'],a['gen'],a['br'],a['base'],a['cost']
    n,ng=len(bus),len(g)
    eliminated={}
    selected={}
    degree=np.bincount(np.r_[a['fr'],a['to']],minlength=n)
    if policy in ['all','low_degree','full_matched']:
        for i in sorted(set(a['gb'])):
            ids=np.flatnonzero(a['gb']==i)
            selected[i]=max(ids,key=lambda j:(g[j,8]-g[j,9])+(g[j,3]-g[j,4]))
    if policy=='all':eliminated=selected
    if policy=='low_degree':eliminated={i:j for i,j in selected.items() if degree[i]<=3}
    free=[j for j in range(ng) if j not in eliminated.values()]
    v=ca.SX.sym('V',n);ang=ca.SX.sym('theta',n)
    pg=ca.SX.sym('pg',len(free));qg=ca.SX.sym('qg',len(free))
    x=ca.vertcat(v,ang,pg,qg)
    P=dict(zip(free,ca.vertsplit(pg)));Q=dict(zip(free,ca.vertsplit(qg)))
    reqp=[bus[i,2]/b+bus[i,4]/b*v[i]**2 for i in range(n)]
    reqq=[bus[i,3]/b-bus[i,5]/b*v[i]**2 for i in range(n)]
    rows=[];lo=[];hi=[]
    def row(expr,lb,ub):
        rows.append(expr);lo.append(lb);hi.append(ub)
    for k,(i,j) in enumerate(zip(a['fr'],a['to'])):
        da=ang[i]-ang[j]
        for u,w,delta,selfy,other in [(i,j,da,a['yff'][k],a['yft'][k]),
                                      (j,i,-da,a['ytt'][k],a['ytf'][k])]:
            pp=selfy.real*v[u]**2+v[u]*v[w]*(other.real*ca.cos(delta)+other.imag*ca.sin(delta))
            qq=-selfy.imag*v[u]**2+v[u]*v[w]*(other.real*ca.sin(delta)-other.imag*ca.cos(delta))
            reqp[u]+=pp;reqq[u]+=qq
            if br[k,5]>0: row(pp**2+qq**2,-np.inf,(br[k,5]/b)**2)
        row(da,np.deg2rad(br[k,11]),np.deg2rad(br[k,12]))
    for i in range(n):
        ids=np.where(a['gb']==i)[0]
        others=[j for j in ids if j in free]
        pp=reqp[i]-sum(P[j] for j in others)
        qq=reqq[i]-sum(Q[j] for j in others)
        if i in eliminated:
            j=eliminated[i];P[j]=pp;Q[j]=qq
            row(pp,g[j,9]/b,g[j,8]/b);row(qq,g[j,4]/b,g[j,3]/b)
        else:
            row(pp,0.,0.);row(qq,0.,0.)
    pv=ca.vertcat(*(b*P[j] for j in range(ng)));qv=ca.vertcat(*(b*Q[j] for j in range(ng)))
    unpack=ca.Function('unpack',[x],[v,ang,pv,qv])
    objective=sum(coef[j,0]*pv[j]**2+coef[j,1]*pv[j]+coef[j,2] for j in range(ng))
    scale=max(1,sum(bus[:,2])*40)
    constraints=ca.vertcat(*rows)
    v0,a0,p0,q0=starts(a,policy!='full_flat')
    if policy=='full_matched':
        volt=v0*np.exp(1j*a0)
        demand=(bus[:,2]+1j*bus[:,3])/b+(bus[:,4]-1j*bus[:,5])/b*v0**2
        for side,other,y1,y2 in [(a['fr'],a['to'],a['yff'],a['yft']),(a['to'],a['fr'],a['ytt'],a['ytf'])]:
            np.add.at(demand,side,volt[side]*np.conj(y1*volt[side]+y2*volt[other]))
        for i,j in selected.items():
            ids=np.flatnonzero((a['gb']==i)&(np.arange(ng)!=j))
            residual=demand[i]-sum(p0[ids]+1j*q0[ids])
            p0[j],q0[j]=residual.real,residual.imag
    initial_box=max(0.,max(p0*b-g[:,8]),max(g[:,9]-p0*b),max(q0*b-g[:,3]),max(g[:,4]-q0*b))
    guess=np.r_[v0,a0,p0[free],q0[free]]
    angle_lo=np.full(n,-np.pi*2);angle_hi=-angle_lo
    angle_lo[a['ref']]=angle_hi[a['ref']]=0.
    opts={**opts,'ipopt.max_wall_time':max(.001,CFG['seconds_per_policy']-(time.perf_counter()-start))}
    solver=ca.nlpsol('s','ipopt',{'x':x,'f':objective/scale,'g':constraints},opts)
    dims=dict(n_variables=x.numel(),constraint_rows=len(rows),jacobian_nnz=ca.jacobian(constraints,x).nnz())
    build=time.perf_counter()-start
    result=solver(x0=guess,lbx=np.r_[bus[:,12],angle_lo,g[free,9]/b,g[free,4]/b],
                  ubx=np.r_[bus[:,11],angle_hi,g[free,8]/b,g[free,3]/b],lbg=lo,ubg=hi)
    vals=[np.asarray(z).ravel() for z in unpack(result['x'])]
    solved=time.perf_counter()-start
    check=independent(a,*vals)
    elapsed=time.perf_counter()-start
    record=dict(case=path.stem,policy=policy,repeat=rep,**dims,status=solver.stats()['return_status'],
                iterations=solver.stats()['iter_count'],build_seconds=build,solve_s=solved-build,
                validation_s=elapsed-solved,elapsed=elapsed,within_deadline=elapsed<=12,check=check,
                reconstructed_start_box_MW_MVAr=initial_box,rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                options=opts,variables=vals)
    try:record['lower']=dispatch_floor(a)
    except ValueError as exc:record['lower_unavailable']=str(exc)
    changed=[val.copy() for val in vals];changed[2][0]+=1.
    record['corrupt_rejected']=not independent(a,*changed)['valid']
    if rep==0:
        details,pattern=probe(x,constraints,objective/scale,result);record['structure']=details
        np.savez_compressed(out/(path.stem+'_'+policy+'_pattern.npz'),**pattern)
    return record

def run():
    _,action,*args=sys.argv
    if action=='one':
        path,policy,rep,out=args;out=Path(out)
        opts=dict(json.loads((HERE.parent/'foundation/results/C/development.json').read_text())['trials'][0]['options'])
        opts['ipopt.mu_strategy']=json.loads((HERE.parent/'foundation/results/C/development.json').read_text())['mu_strategy']
        try:r=solve(Path(path),policy,int(rep),opts,out)
        except Exception as exc:r=dict(case=Path(path).stem,policy=policy,repeat=int(rep),error=repr(exc))
        save(out/(Path(path).stem+'_'+policy+'_'+rep+'.json'),r)
    else:
        out=Path(args[0]);out.mkdir(parents=True,exist_ok=True)
        if list(out.glob('*.json')):raise ValueError('Use a fresh output directory')
        cases=sorted((HERE/'inputs').glob('*.m')) if action=='run' else [HERE.parent/'foundation/inputs/ac/pglib_opf_case14_ieee__api.m']
        for j,p in enumerate(cases):
            for rep in range(5 if action=='run' else 1):
                arms=['full_dc','full_matched','all','low_degree'];k=(j+rep)%4
                for arm in arms[k:]+arms[:k]:
                    # Allow post-clock diagnostics after the strict 12-second scoring gate.
                    try:subprocess.run([sys.executable,__file__,'one',str(p),arm,str(rep),str(out)],timeout=110,check=True)
                    except (subprocess.TimeoutExpired,subprocess.CalledProcessError) as exc:
                        save(out/(p.stem+'_'+arm+'_'+str(rep)+'.json'),dict(case=p.stem,policy=arm,repeat=rep,error=type(exc).__name__))
            print(p.stem,flush=True)
if __name__=='__main__':run()
