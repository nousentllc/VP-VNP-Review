"""Exact fixed-mode synthetic fleet. Magnitudes are MW over one-hour intervals."""
from fractions import Fraction as F
import random
import numpy as np

def zeros(shape):
    return np.full(shape,F(0),dtype=object)

def fleet(seed,regime,n=3,T=8):
    rng=random.Random(seed)
    N=n*T;I=zeros((N,N));np.fill_diagonal(I,F(1))
    cap=[F(rng.randint(5,9)) for _ in range(n)]
    eta_c=[F(89+i*2,100) for i in range(n)];eta_d=[F(91+i,100) for i in range(n)]
    signs=[[(1 if ((t//2+i)%2==0) else -1) for t in range(T)] for i in range(n)]
    anchor=zeros(N);avail=[True]*N;limits=zeros(N);U=zeros(N);c=zeros(N)
    price=[F([15,63,82,-17,33,91,22,68][t%8]+rng.randint(-5,5)) for t in range(T)]
    net=zeros((T,N));energy=zeros((n,T,N));initial=[F(19+i) for i in range(n)]
    A=[];b=[];labels=[];E=[];d=[]
    def add(row,upper,name):
        A.append(row.copy());b.append(F(upper));labels.append(name)
    for i in range(n):
        for t in range(T):
            j=i*T+t;q=signs[i][t]
            avail[j]=not (regime=='outage' and (t==2+i or (i==0 and t==3)))
            reserve=F(1) if (i+t)%3==0 and q<0 else F(0)
            U[j]=cap[i];limits[j]=max(F(0),cap[i]*int(avail[j])-reserve)
            anchor[j]=min(limits[j],F(rng.randint(2,4)))
            net[t,j]=q
            energy[i,t:,j]=eta_c[i] if q>0 else -1/eta_d[i]
            c[j]=q*price[t]+F(5+i,4)
            add(I[j],limits[j],f'power_{i}_{t}');add(-I[j],0,f'nonneg_{i}_{t}')
        for t in range(T):
            v=energy[i,t];add(v,38-initial[i],f'soc_cap_{i}_{t}')
            floor=F(6+(3 if t in (4,5) else 0))
            add(-v,initial[i]-floor,f'reserve_soc_{i}_{t}')
        end=energy[i,-1];target=end@anchor
        if i%2==0 or regime=='tight':E.append(end.copy());d.append(target)
        else:add(end,target+F(3,4),f'terminal_max_{i}');add(-end,-target+F(3,4),f'terminal_min_{i}')
    load=[F(27+rng.randint(-4,4)) for _ in range(T)]
    # Margins are constructed around the feasible reference. All arms face the resulting same rows.
    delta={'slack':F(8),'tight':F(1,2),'boundary':F(2),'outage':F(3)}[regime]
    for t,g in enumerate(net):
        grid=load[t]+g@anchor;prevload=load[t-1] if t else load[0]
        dg=g-net[t-1] if t else g
        prevgrid=load[t-1]+net[t-1]@anchor if t else load[0]
        component=dg@anchor
        add(g,grid-load[t]+(0 if regime=='boundary' and t%2==0 else delta),f'grid_import_{t}')
        add(-g,-grid+load[t]+delta,f'grid_min_{t}')
        # A symmetric ramp around zero on physical net imports. Load steps are included.
        rlimit=abs(grid-prevgrid)+(0 if regime=='boundary' and t%2==1 else delta)
        add(dg,rlimit-(load[t]-prevload),f'ramp_up_{t}')
        add(-dg,rlimit+(load[t]-prevload),f'ramp_down_{t}')
    A=np.array(A,dtype=object);b=np.array(b,dtype=object);E=np.array(E,dtype=object);d=np.array(d,dtype=object)
    assert max(A@anchor-b)<=0 and all(E@anchor==d)
    groups=[list(range(i*T+t,i*T+min(T,t+2))) for i in range(n) for t in range(0,T,2)]
    S=zeros((N,len(groups)));G=zeros((len(groups),N))
    for k,group in enumerate(groups):
        assert len({signs[j//T][j%T] for j in group})==1
        for j in group:S[j,k]=F(1);G[k,j]=F(1,len(group))
    return dict(A=A,b=b,E=E,d=d,c=c,cap=U,x0=anchor,S=S,G=G,labels=labels,energy=energy,n=n,T=T,
                initial=initial,load=load,price=price,eta_c=eta_c,eta_d=eta_d,signs=signs,availability=avail)
