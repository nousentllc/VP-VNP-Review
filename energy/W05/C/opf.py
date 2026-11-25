import sys,resource,json,time,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
W04=HERE.parents[1]/'W04'
sys.path.insert(0,str(W04/'foundation/src'))
sys.path.insert(0,str(W04/'C'))
from selection import select,common_start
from review_check import get_network
from ac import read_case,starts,independent,dispatch_floor,ca,np,save,CFG
from structure import probe
def solve(path,policy,rep,opts,out):
    start=time.perf_counter()
    a=read_case(path)
    bus,g,br,b,coef=a['bus'],a['gen'],a['br'],a['base'],a['cost']
    n,ng=len(bus),len(g)
    select_start=time.perf_counter()
    eliminated,scores=select(a,policy)
    select_s=time.perf_counter()-select_start
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
    if policy!='full_dc':p0,q0=common_start(a,v0,a0,p0,q0)
    initial_box=max(0.,max(p0*b-g[:,8]),max(g[:,9]-p0*b),max(q0*b-g[:,3]),max(g[:,4]-q0*b))
    guess=np.r_[v0,a0,p0[free],q0[free]]
    initial=[np.asarray(t).ravel() for t in unpack(guess)]
    start_lift_mismatch=max(np.max(abs(initial[2]-b*p0)),np.max(abs(initial[3]-b*q0)))
    if start_lift_mismatch>1e-6:raise ValueError('Lifted initial state mismatch')
    angle_lo=np.full(n,-np.pi*2);angle_hi=-angle_lo
    angle_lo[a['ref']]=angle_hi[a['ref']]=0.
    opts={**opts,'ipopt.max_wall_time':max(.001,CFG['seconds_per_policy']-(time.perf_counter()-start))}
    log_path=out/(path.stem+'_'+policy+'_'+str(rep)+'.ipopt')
    opts.update({'ipopt.print_timing_statistics':'yes','ipopt.timing_statistics':'yes',
                 'ipopt.output_file':str(log_path.resolve()),'ipopt.file_print_level':5})
    solver=ca.nlpsol('s','ipopt',{'x':x,'f':objective/scale,'g':constraints},opts)
    dims=dict(n_variables=x.numel(),constraint_rows=len(rows),jacobian_nnz=ca.jacobian(constraints,x).nnz())
    build=time.perf_counter()-start
    result=solver(x0=guess,lbx=np.r_[bus[:,12],angle_lo,g[free,9]/b,g[free,4]/b],
                  ubx=np.r_[bus[:,11],angle_hi,g[free,8]/b,g[free,3]/b],lbg=lo,ubg=hi)
    vals=[np.asarray(z).ravel() for z in unpack(result['x'])]
    solved=time.perf_counter()-start
    audit=get_network(path)[-1]
    check=audit(*vals)
    elapsed=time.perf_counter()-start
    record=dict(case=path.stem,policy=policy,repeat=rep,**dims,status=solver.stats()['return_status'],
                iterations=solver.stats()['iter_count'],build_seconds=build,solve_s=solved-build,
                validation_s=elapsed-solved,elapsed=elapsed,within_deadline=elapsed<=12,check=check,
                reconstructed_start_box_MW_MVAr=initial_box,rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                options={k:v for k,v in opts.items() if k!='ipopt.output_file'},variables=vals,
                pivots=eliminated,scores=scores,selection_s=select_s,start_lift_mismatch=start_lift_mismatch,
                initial_vectors=initial if rep==0 else None,host_load=__import__('os').getloadavg())
    try:record['lower']=dispatch_floor(a)
    except ValueError as exc:record['lower_unavailable']=str(exc)
    changed=[val.copy() for val in vals];changed[2][0]+=1.
    record['corrupt_rejected']=not audit(*changed)['valid']
    if rep==0:
        details,pattern=probe(x,constraints,objective/scale,result);record['structure']=details
        np.savez_compressed(out/(path.stem+'_'+policy+'_pattern.npz'),**pattern)
    return record

def log_summary(path):
    """IPOPT internal timing CPU/system/wall; retain raw log for scalar interpretation."""
    import re
    result={}
    if path.exists():
        for line in path.read_text(errors='replace').splitlines():
            m=re.match(r'\s*(LinearSystemSymbolicFactorization|LinearSystemFactorization|LinearSystemBackSolve|PDSystemSolverTotal)\.*\s*:\s*([\d.]+)\s*\(sys:\s*([\d.]+)\s*wall:\s*([\d.]+)\)',line)
            if m:result[m[1]]={'cpu_s':float(m[2]),'sys_s':float(m[3]),'wall_s':float(m[4])}
    return result

def main():
    import hashlib,datetime
    read_digest=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
    arms=['full_dc','full_matched','all','degree','guided']
    act,out=sys.argv[1],Path(sys.argv[2]);cases=sorted((HERE/'inputs').glob('*.m'))
    files=[HERE/'opf.py',HERE/'selection.py',HERE/'plan.md',W04/'C/structure.py',W04/'C/review_check.py',
           W04/'foundation/src/ac.py',W04/'foundation/results/C/development.json',*cases]
    if act=='freeze':
        if out.exists():raise ValueError('lock exists')
        out.write_text(json.dumps(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),arms=arms,repeats=5,gate_s=12,
                    hashes={str(q.relative_to(W04.parent)):read_digest(q) for q in files}),indent=2)+'\n');return
    if act=='one':
        path,policy,rep=Path(sys.argv[3]),sys.argv[4],int(sys.argv[5])
        cfg=json.loads((W04/'foundation/results/C/development.json').read_text())
        opts=dict(cfg['trials'][0]['options']);opts['ipopt.mu_strategy']=cfg['mu_strategy']
        try:
            r=solve(path,policy,rep,opts,out)
            r['native_timing']=log_summary(out/(path.stem+'_'+policy+'_'+str(rep)+'.ipopt'))
        except Exception as e:
            import traceback
            r=dict(case=path.stem,policy=policy,repeat=rep,error=repr(e),detail=traceback.format_exc())
        save(out/(path.stem+'_'+policy+'_'+str(rep)+'.json'),r);return
    out.mkdir(parents=True,exist_ok=False)
    if act=='dev':cases=[W04/'C/inputs/pglib_opf_case57_ieee.m']
    else:
        lock=json.loads((HERE/'freeze.json').read_text())
        assert act=='run' and all(read_digest(q)==lock['hashes'][str(q.relative_to(W04.parent))] for q in files)
    # Interleave sites in each repeat. One AC worker at a time. Imports excluded from scoring.
    for rep in range(1 if act=='dev' else 5):
        for j,p in enumerate(cases[rep%len(cases):]+cases[:rep%len(cases)]):
            k=(j+rep)%len(arms)
            for policy in arms[k:]+arms[:k]:
                try:subprocess.run([sys.executable,__file__,'one',str(out),str(p),policy,str(rep)],timeout=100,check=True)
                except (subprocess.TimeoutExpired,subprocess.CalledProcessError) as exc:
                    save(out/(p.stem+'_'+policy+'_'+str(rep)+'.json'),dict(case=p.stem,policy=policy,repeat=rep,error=repr(exc)))
            print(rep,p.stem,flush=True)
if __name__=='__main__':main()
