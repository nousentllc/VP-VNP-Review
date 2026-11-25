"""PGLib AC network in exact decimal inputs, Arb admittances, and a full polar local baseline."""
from fractions import Fraction as F
import re
import time
import math
import numpy as np
import casadi as ca
from flint import ctx, arb, acb, fmpq
ctx.prec=160


def ball(v):
    v=F(v);return arb(fmpq(v.numerator,v.denominator))


def lower(v):
    return F(str(v.lower().fmpq()))


def upper(v):
    return F(str(v.upper().fmpq()))


class Grid:
    def __init__(self,path):
        text=re.sub(r'%[^\n]*','',path.read_text())
        def table(name):
            block=re.search(r'mpc\.'+name+r'\s*=\s*\[(.*?)\];',text,re.S)[1]
            return [[F(v) for v in s.split()] for s in block.split(';') if s.strip()]
        self.b=F(re.search(r'mpc.baseMVA\s*=\s*([.\d]+)',text)[1])
        self.bus=table('bus');gens=table('gen');costs=table('gencost')
        assert len(gens)==len(costs) and all(c[0]==2 and c[3]==3 and c[4]>=0 for c in costs)
        self.gen=[g for g in gens if g[7]>0];self.cost=[c[4:7] for g,c in zip(gens,costs) if g[7]>0]
        self.branch=[b for b in table('branch') if b[10]>0]
        self.n=len(self.bus);self.ng=len(self.gen);idx={a[0]:i for i,a in enumerate(self.bus)}
        refs=[i for i,b in enumerate(self.bus) if b[1]==3]
        assert len(refs)==1
        self.ref=refs[0];self.gb=[idx[g[0]] for g in self.gen];self.edges=[]
        self.Y=[{} for _ in self.bus]
        for line in self.branch:
            i,j=idx[line[0]],idx[line[1]];y=1/acb(ball(line[2]),ball(line[3]))
            charging=acb(0,ball(line[4]/2));mag=line[8] or F(1)
            angle=ball(line[9])*arb.pi()/180
            tap=ball(mag)*acb(angle.cos(),angle.sin())
            ff=(y+charging)/ball(mag*mag);tt=y+charging;ft=-y/tap.conjugate();tf=-y/tap
            self.edges.append((i,j,ff,ft,tf,tt))
            for u,v,z in [(i,i,ff),(i,j,ft),(j,i,tf),(j,j,tt)]:
                self.Y[u][v]=self.Y[u].get(v,0)+z
        for i,b in enumerate(self.bus):
            self.Y[i][i]+=acb(ball(b[4]/self.b),ball(b[5]/self.b))

    def baseline(self,mode):
        start=time.perf_counter()
        n,ng=self.n,self.ng
        b=float(self.b);bus=np.array(self.bus,float);gen=np.array(self.gen,float)
        vm=ca.SX.sym('vm',n);va=ca.SX.sym('va',n);pg=ca.SX.sym('pg',ng);qg=ca.SX.sym('qg',ng)
        reqp=[bus[i,2]/b+bus[i,4]/b*vm[i]**2 for i in range(n)]
        reqq=[bus[i,3]/b-bus[i,5]/b*vm[i]**2 for i in range(n)]
        cons=[];lo=[];hi=[]
        def add(z,l,u):cons.append(z);lo.append(l);hi.append(u)
        for line,(i,j,ff,ft,tf,tt) in zip(self.branch,self.edges):
            da=va[i]-va[j]
            for u,v,d,aa,ab in ((i,j,da,ff,ft),(j,i,-da,tt,tf)):
                A,B=complex(aa),complex(ab)
                p=A.real*vm[u]**2+vm[u]*vm[v]*(B.real*ca.cos(d)+B.imag*ca.sin(d))
                q=-A.imag*vm[u]**2+vm[u]*vm[v]*(B.real*ca.sin(d)-B.imag*ca.cos(d))
                reqp[u]+=p;reqq[u]+=q
                if line[5]>0:add(p*p+q*q,-np.inf,(float(line[5])/b*(1-1e-5))**2)
            l,u=map(math.radians,map(float,line[11:13]))
            eps=min(1e-6,(u-l)*.1);add(da,l+eps,u-eps)
        for j,i in enumerate(self.gb):reqp[i]-=pg[j];reqq[i]-=qg[j]
        for z in reqp+reqq:add(z,0,0)
        cost=sum(float(c[0])*(pg[j]*b)**2+float(c[1])*pg[j]*b+float(c[2]) for j,c in enumerate(self.cost))
        def inner(l,u,eps):
            delta=np.minimum(eps,.1*(u-l))
            return l+delta,u-delta
        vl,vu=inner(bus[:,12],bus[:,11],2e-5)
        pl,pu=inner(gen[:,9]/b,gen[:,8]/b,2e-5)
        ql,qu=inner(gen[:,4]/b,gen[:,3]/b,2e-5)
        al=np.full(n,-2*np.pi);au=-al;al[self.ref]=au[self.ref]=0
        theta=np.zeros(n);p0=(pl+pu)/2
        if mode=='dc':
            p0=pl.copy();rem=sum(bus[:,2])/b-p0.sum()
            for j in np.argsort([float(c[1]+c[0]*(g[8]+g[9])) for c,g in zip(self.cost,self.gen)]):
                change=np.clip(rem,0,pu[j]-p0[j]);p0[j]+=change;rem-=change
            incidence=np.zeros((len(self.edges),n))
            for k,(i,j,*_) in enumerate(self.edges):incidence[k,i]=1;incidence[k,j]=-1
            w=np.array([1/float(br[3]*(br[8] or 1)) for br in self.branch])
            B=incidence.T@(w[:,None]*incidence);rhs=-bus[:,2]/b
            np.add.at(rhs,self.gb,p0);rhs+=incidence.T@(w*np.radians([float(br[9]) for br in self.branch]))
            keep=np.arange(n)!=self.ref;theta[keep]=np.linalg.solve(B[np.ix_(keep,keep)],rhs[keep])
        scale=max(1,40*sum(bus[:,2]))
        solver=ca.nlpsol('s','ipopt',dict(x=ca.vertcat(vm,va,pg,qg),f=cost/scale,g=ca.vertcat(*cons)),
              {'print_time':False,'ipopt.sb':'yes','ipopt.print_level':0,'ipopt.max_wall_time':30.,'ipopt.tol':1e-10,'ipopt.max_iter':700,'ipopt.bound_relax_factor':0.,'error_on_fail':False})
        t=time.perf_counter()
        res=solver(lbx=np.r_[vl,al,pl,ql],ubx=np.r_[vu,au,pu,qu],lbg=lo,ubg=hi,x0=np.r_[np.clip(np.ones(n),vl,vu),theta,p0,np.clip(np.zeros(ng),ql,qu)])
        end=time.perf_counter();a=np.asarray(res['x']).ravel()
        V=a[:n]*np.exp(1j*a[n:2*n]);g=a[2*n:]
        point=np.r_[V.real,V.imag,g].tolist()
        return dict(mode=mode,point=point,status=solver.stats()['return_status'],iterations=solver.stats()['iter_count'],objective=float(res['f'])*scale,build_s=t-start,solve_s=end-t)
