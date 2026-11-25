"""Rational outer cuts on lifted voltage products, apparent-power disks and convex fuel curves."""
from fractions import Fraction as F
import math
from scipy.optimize import minimize_scalar
from network import ball,upper
from linear import Linear


def quant(x,d=10**7):
    return F(round(float(x)*d),d)


def copper(g):
    # Nonnegative aggregate losses imply sum(Pg)>=demand; support the resulting inequality at a nonnegative price.
    if any(b[4]<0 for b in g.bus) or any(b[2]<0 for b in g.branch):return None,None
    def dual(lam):
        lam=F(lam);assert lam>=0
        L=lam*sum(b[2] for b in g.bus)
        for (a,b,c),gen in zip(g.cost,g.gen):
            l,h=gen[9],gen[8]
            p=max(l,min(h,(lam-b)/(2*a))) if a else (l if b>=lam else h)
            L+=a*p*p+(b-lam)*p+c
        return L
    cap=max(F(1),max(2*a*gen[8]+b for (a,b,_),gen in zip(g.cost,g.gen))+1)
    fit=minimize_scalar(lambda x:-float(dual(quant(x))),bounds=(0.,float(cap)),method='bounded')
    lam=max([F(0),cap,quant(fit.x)],key=dual)
    return dual(lam),lam


class Outer:
    def __init__(self,g):
        self.g=g;self.lp=lp=Linear();self.keys=set();self.cuts=[]
        self.w=[lp.var(f'w{i}',v[12]**2,v[11]**2) for i,v in enumerate(g.bus)]
        self.pairs={};self.pg=[];self.qg=[];self.z=[];self.flow=[]
        pbal=[{self.w[i]:-b[4]} for i,b in enumerate(g.bus)]
        qbal=[{self.w[i]:b[5]} for i,b in enumerate(g.bus)]
        for j,(v,(a,b,c)) in enumerate(zip(g.gen,g.cost)):
            p=lp.var(f'p{j}',v[9],v[8]);q=lp.var(f'q{j}',v[4],v[3])
            ends=[a*t*t+b*t+c for t in (v[9],v[8])]
            mincost=min(ends+[c-b*b/(4*a)] if a else ends)
            z=lp.var(f'cost{j}',mincost,max(ends),1)
            self.pg.append(p);self.qg.append(q);self.z.append(z)
            pbal[g.gb[j]][p]=1;qbal[g.gb[j]][q]=1
            for t in [v[9],v[8],(v[8]+v[9])/2]:self.cut('cost',j,t)
        for k,((i,j,ff,ft,tf,tt),br) in enumerate(zip(g.edges,g.branch)):
            a,b=sorted([i,j]);pair=(a,b);m=g.bus[i][11]*g.bus[j][11]
            if pair not in self.pairs:
                zr=lp.var(f're{a}_{b}',-m,m);zi=lp.var(f'im{a}_{b}',-m,m)
                self.pairs[pair]=(zr,zi)
                self.cut('soc',pair,F(1),F(0))
            zr,zi=self.pairs[pair];orient=1 if i==a else -1
            for u,v,aa,ab,sgn,balp,balq in [(i,j,ff,ft,orient,pbal[i],qbal[i]),(j,i,tt,tf,-orient,pbal[j],qbal[j])]:
                cap=br[5] if br[5]>0 else math.ceil(upper(ball(g.b*g.bus[u][11])*(abs(aa)*ball(g.bus[u][11])+abs(ab)*ball(g.bus[v][11]))))
                p=lp.var('P'+str(k)+'_'+str(u),-cap,cap);q=lp.var('Q'+str(k)+'_'+str(u),-cap,cap)
                self.flow.append((p,q,br[5]));balp[p]=-1;balq[q]=-1
                for col,terms in [(p,[(self.w[u],aa.real),(zr,ab.real),(zi,sgn*ab.imag)]),
                                  (q,[(self.w[u],-aa.imag),(zr,-ab.imag),(zi,sgn*ab.real)])]:
                    co={col:F(1)};error=F(0)
                    for idx,coeff in terms:
                        exact=coeff*ball(g.b);center=quant(exact,10**12);co[idx]=-center
                        # The row slack encloses coefficient rounding for every point of its box.
                        error+=upper(abs(exact-ball(center)))*max(abs(t) for t in lp.box[idx])
                    # Round the slack OUT to a compact decimal rational.
                    e=F(math.ceil(error*10**12),10**12)
                    lp.row(f'flow{col}',co,-e,e)
        for i,b in enumerate(g.bus):
            lp.row('P'+str(i),pbal[i],b[2],b[2]);lp.row('Q'+str(i),qbal[i],b[3],b[3])
        # Angle and cycle constraints may be dropped in an outer approximation.

    def cut(self,kind,obj,*v):
        key=(kind,obj,*v)
        if key in self.keys:return
        self.keys.add(key);self.cuts.append([kind,list(obj) if isinstance(obj,tuple) else obj,*map(str,v)])
        g=self.g;lp=self.lp;name=kind+str(len(self.cuts))
        if kind=='cost':
            t,=v;a,b,c=g.cost[obj]
            lp.row(name,{self.z[obj]:1,self.pg[obj]:-(2*a*t+b)},c-a*t*t,None)
        elif kind=='soc':
            i,j=obj;p,q=v;zr,zi=self.pairs[obj]
            lp.row(name,{self.w[i]:1,self.w[j]:p*p+q*q,zr:-2*p,zi:-2*q},0,None)
        elif kind=='thermal':
            p,q=v;P,Q,r=self.flow[obj]
            assert r>0
            lp.row(name,{P:2*p,Q:2*q},None,r*(1+p*p+q*q))
        else:raise ValueError(kind)

    def refine(self,x):
        for pair,(z,y) in self.pairs.items():
            j=pair[1];w=x[self.w[j]]
            self.cut('soc',pair,quant(x[z]/w),quant(x[y]/w))
        for j,(p,q,rate) in enumerate(self.flow):
            d=math.hypot(x[p],x[q])
            if rate>0 and d>0.95*float(rate):self.cut('thermal',j,quant(x[p]/d),quant(x[q]/d))
        for j,p in enumerate(self.pg):
            if self.g.cost[j][0]:self.cut('cost',j,quant(x[p]))

    def seed(self,point):
        n=self.g.n;v=[complex(point[i],point[n+i]) for i in range(n)]
        for i,j in self.pairs:
            k=v[i]/v[j];self.cut('soc',(i,j),quant(k.real),quant(k.imag))
        for j in range(self.g.ng):
            if self.g.cost[j][0]:self.cut('cost',j,quant(point[2*n+j]*float(self.g.b)))
        for k,(i,j,ff,ft,tf,tt) in enumerate(self.g.edges):
            if self.g.branch[k][5]<=0:continue
            for side,flow in enumerate([v[i]*(complex(ff)*v[i]+complex(ft)*v[j]).conjugate(),v[j]*(complex(tf)*v[i]+complex(tt)*v[j]).conjugate()]):
                if abs(flow):
                    unit=flow/abs(flow);self.cut('thermal',2*k+side,quant(unit.real),quant(unit.imag))
