"""PGLib AC optimal power flow with exact generator elimination and independent AC replay."""
import json
import re
import time
import numpy as np
import casadi as ca
from scipy.optimize import minimize_scalar
from common import DESIGN, ROOT, OUT, save

CFG=DESIGN['C']


def read_case(path):
    s=re.sub(r'%[^\n]*','',path.read_text())
    def mat(key):
        part=re.search(r'mpc\.'+key+r'\s*=\s*\[(.*?)\];',s,re.S)[1]
        return np.array([[float(v) for v in row.split()] for row in part.split(';') if row.strip()])
    bus,gen,br,cost=map(mat,['bus','gen','branch','gencost'])
    on=gen[:,7]>0
    if len(cost)!=len(gen) or not np.all(cost[:,0]==2) or not np.all(cost[:,3]==3):
        raise ValueError('Unsupported generator cost')
    gen,cost,br=gen[on],cost[on,4:7],br[br[:,10]>0]
    b=float(re.search(r'mpc.baseMVA\s*=\s*([.\d]+)',s)[1])
    idx={int(v):i for i,v in enumerate(bus[:,0])}
    gb=np.array([idx[int(v)] for v in gen[:,0]])
    fr=np.array([idx[int(v)] for v in br[:,0]])
    to=np.array([idx[int(v)] for v in br[:,1]])
    ref=np.where(bus[:,1]==3)[0]
    if len(ref)!=1: raise ValueError('Connected single-reference cases required')
    tap=np.where(br[:,8]==0,1,br[:,8])*np.exp(1j*np.deg2rad(br[:,9]))
    line=1/(br[:,2]+1j*br[:,3])
    yff=(line+1j*br[:,4]/2)/abs(tap)**2
    ytt=line+1j*br[:,4]/2
    return dict(bus=bus,gen=gen,br=br,cost=cost,base=b,gb=gb,fr=fr,to=to,ref=int(ref[0]),
                yff=yff,ytt=ytt,yft=-line/np.conjugate(tap),ytf=-line/tap)


def independent(a,v,angle,p,q):
    bus,br,b=a['bus'],a['br'],a['base']
    net=np.zeros(len(bus),complex)
    volt=v*np.exp(1j*angle)
    worst_heat=worst_angle=0.
    for row,i,j in zip(br,a['fr'],a['to']):
        y=1/complex(row[2],row[3])
        tap=(row[8] or 1.)*np.exp(1j*np.deg2rad(row[9]))
        internal=volt[i]/tap
        series=(internal-volt[j])*y
        sf=b*internal*np.conj(series+internal*(1j*row[4]/2))
        st=b*volt[j]*np.conj(-series+volt[j]*(1j*row[4]/2))
        net[i]+=sf;net[j]+=st
        if row[5]>0:worst_heat=max(worst_heat,abs(sf)-row[5],abs(st)-row[5])
        diff=np.rad2deg(angle[i]-angle[j])
        worst_angle=max(worst_angle,row[11]-diff,diff-row[12])
    net+=(bus[:,4]-1j*bus[:,5])*v**2
    supply=np.zeros(len(bus),complex)
    np.add.at(supply,a['gb'],p+1j*q)
    mismatch=supply-(bus[:,2]+1j*bus[:,3])-net
    gen=a['gen'];coef=a['cost']
    box=max(0.,max(gen[:,9]-p),max(p-gen[:,8]),max(gen[:,4]-q),max(q-gen[:,3]))
    vm=max(0.,max(bus[:,12]-v),max(v-bus[:,11]))
    balance=max(max(abs(mismatch.real)),max(abs(mismatch.imag)))
    valid=(max(balance,worst_heat,box)<=CFG['physics_tol_MVA'] and vm<=1e-7 and
           worst_angle<=CFG['angle_tol_deg'] and abs(angle[a['ref']])<1e-7)
    return dict(valid=bool(valid),balance_MVA=balance,thermal_MVA=worst_heat,angle_degrees=worst_angle,
                generator_box_MW_MVAr=box,voltage_pu=vm,cost=float(np.sum(coef[:,0]*p*p+coef[:,1]*p+coef[:,2])))


def dispatch_floor(a):
    gen,coef=a['gen'],a['cost']
    lo,hi=gen[:,9],gen[:,8]
    if np.any(coef[:,0]<0) or np.any(a['bus'][:,4]<0) or np.any(a['br'][:,2]<0):
        raise ValueError('The dispatch floor requires convex costs and nonnegative losses/shunts')
    def support(price):
        quad=coef[:,0]>0
        p=np.where(coef[:,1]>=price,lo,hi).copy()
        p[quad]=np.clip((price-coef[quad,1])/(2*coef[quad,0]),lo[quad],hi[quad])
        return price*sum(a['bus'][:,2])+sum(coef[:,0]*p*p+(coef[:,1]-price)*p+coef[:,2])
    upper=max(1.,max(2*coef[:,0]*hi+coef[:,1])+1)
    sol=minimize_scalar(lambda price:-support(price),bounds=(0,upper),method='bounded')
    value=max(support(0),support(upper),support(sol.x))
    return value-1e-9*max(1,abs(value))


def starts(a,warm):
    b,bus,g,br=a['base'],a['bus'],a['gen'],a['br']
    p=(g[:,9]+g[:,8])/2
    q=np.clip(np.zeros(len(g)),g[:,4],g[:,3])
    theta=np.zeros(len(bus))
    if warm:
        p=g[:,9].copy()
        rem=sum(bus[:,2])-sum(p)
        for i in np.argsort(a['cost'][:,1]+a['cost'][:,0]*(g[:,9]+g[:,8])):
            add=np.clip(rem,0,g[i,8]-p[i]);p[i]+=add;rem-=add
        incidence=np.zeros((len(br),len(bus)))
        incidence[np.arange(len(br)),a['fr']]=1
        incidence[np.arange(len(br)),a['to']]=-1
        weights=1/(br[:,3]*np.where(br[:,8]==0,1,br[:,8]))
        B=incidence.T@(weights[:,None]*incidence)
        injection=-bus[:,2]/b;np.add.at(injection,a['gb'],p/b)
        rhs=injection+incidence.T@(weights*np.deg2rad(br[:,9]))
        keep=np.arange(len(bus))!=a['ref']
        theta[keep]=np.linalg.solve(B[np.ix_(keep,keep)],rhs[keep])
    return np.clip(np.ones(len(bus)),bus[:,12],bus[:,11]),theta,p/b,q/b


def solve(path,policy,rep,opts):
    start=time.perf_counter()
    a=read_case(path)
    bus,g,br,b,coef=a['bus'],a['gen'],a['br'],a['base'],a['cost']
    n,ng=len(bus),len(g)
    eliminated={}
    if policy=='eliminate_dc':
        for i in sorted(set(a['gb'])):
            ids=np.flatnonzero(a['gb']==i)
            eliminated[i]=max(ids,key=lambda j:(g[j,8]-g[j,9])+(g[j,3]-g[j,4]))
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
    check=independent(a,*vals)
    elapsed=time.perf_counter()-start
    return dict(case=path.stem,policy=policy,repeat=rep,**dims,status=solver.stats()['return_status'],
                iterations=solver.stats()['iter_count'],build_seconds=build,elapsed=elapsed,
                within_deadline=elapsed<=CFG['seconds_per_policy'],check=check,variables=vals,
                dispatch_lower=dispatch_floor(a),options=opts)


def run():
    out=OUT/'C';out.mkdir(exist_ok=True)
    base={'print_time':False,'ipopt.print_level':0,'ipopt.sb':'yes','ipopt.tol':1e-9,
          'ipopt.constr_viol_tol':1e-9,'ipopt.bound_relax_factor':0.,'ipopt.max_iter':600,
          'ipopt.fixed_variable_treatment':'make_parameter','error_on_fail':False}
    dev=[]
    source=ROOT/'inputs/ac'
    for mu in ['monotone','adaptive']:
        rec=solve(source/'pglib_opf_case3_lmbd.m','full_flat',0,{**base,'ipopt.mu_strategy':mu})
        dev.append(rec)
    selected=min(dev,key=lambda v:(not v['check']['valid'],v['iterations'],v['elapsed']))['options']['ipopt.mu_strategy']
    save(out/'development.json',dict(trials=dev,mu_strategy=selected))
    rows=[]
    for j,path in enumerate(sorted(source.glob('*.m'))):
        if 'case3_lmbd' in path.name:continue
        for rep in range(CFG['repeats']):
            methods=CFG['policies'];k=(rep+j)%len(methods)
            for policy in methods[k:]+methods[:k]:
                try: rows.append(solve(path,policy,rep,{**base,'ipopt.mu_strategy':selected}))
                except Exception as err:
                    rows.append(dict(case=path.stem,repeat=rep,policy=policy,error=str(err)))
    save(out/'runs.json',rows)


if __name__=='__main__':run()
