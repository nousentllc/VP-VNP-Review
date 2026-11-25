"""Static device-pivot choices and a common physical starting tuple."""
import numpy as np

def select(case, policy):
    gen=case['gen']; bus=case['bus'];gb=case['gb'];n=len(bus)
    neighbors=[set() for _ in range(n)]
    for i,j in zip(case['fr'],case['to']):
        neighbors[i].add(j);neighbors[j].add(i)
    count=np.bincount(np.r_[case['fr'],case['to']],minlength=n)
    chosen={};scores={}
    for i in np.unique(gb):
        ids=np.flatnonzero(gb==i)
        span=lambda j:gen[j,8]-gen[j,9]+gen[j,3]-gen[j,4]
        j=max(ids,key=span)
        if policy=='guided':
            around=sorted(neighbors[i]);open_pairs=sum(v not in neighbors[u] for k,u in enumerate(around) for v in around[k+1:])
            # Squaring a reconstructed P can make every pair in its gradient support adjacent.
            k=2+2*len(around)+len(ids)-1
            j=min(ids,key=lambda g:(case['cost'][g,0]!=0,-span(g),int(g)))
            score=open_pairs+(k*(k-1)//2 if case['cost'][j,0]!=0 else 0)
            scores[int(i)]=int(score)
            if score>6:continue
        if policy=='degree' and count[i]>3:continue
        if policy in ('all','degree','guided'):chosen[int(i)]=int(j)
    return chosen,scores

def common_start(a,v,theta,p,q):
    """Give every generator bus net zero initial balance residual before IPOPT pushes."""
    bus,g,base=a['bus'],a['gen'],a['base']
    volt=v*np.exp(1j*theta)
    demand=(bus[:,2]+1j*bus[:,3])/base+(bus[:,4]-1j*bus[:,5])/base*v**2
    for i,j,ys,yo in [(a['fr'],a['to'],a['yff'],a['yft']),(a['to'],a['fr'],a['ytt'],a['ytf'])]:
        np.add.at(demand,i,volt[i]*np.conj(ys*volt[i]+yo*volt[j]))
    p,q=p.copy(),q.copy()
    for b in np.unique(a['gb']):
        ids=np.flatnonzero(a['gb']==b); residual=demand[b]-sum(p[ids]+1j*q[ids])
        for values,capacity,delta in [(p,g[ids,8]-g[ids,9],residual.real),(q,g[ids,3]-g[ids,4],residual.imag)]:
            weights=capacity/sum(capacity) if sum(capacity)>0 else np.full(len(ids),1/len(ids))
            values[ids]+=weights*delta
    return p,q
