"""Individual physics, nested mode restrictions and independent policy validation."""
import numpy as np
from common import LinearModel, DESIGN


def arrays(record):
    return {k: np.asarray(v) if isinstance(v,list) else v for k,v in record.items()}


def validate(a, c, d):
    """Recompute energy, grid and cost from AC-side powers, outside the optimization matrix."""
    ec, ed, initial = (a[k][:,None] for k in ['eta_c','eta_d','initial'])
    energy = initial + np.cumsum(ec*c-d/ed, axis=1)
    grid = a['load'] + np.sum(c-d,axis=0)
    power = a['power'][:,None]*a['availability']
    violations = {
        'power':max(0., np.max(-c),np.max(-d),np.max(c-power),np.max(d-power)),
        'soc':max(0.,np.max(a['floor']-energy),np.max(energy-a['capacity'][:,None])),
        'terminal':max(0.,np.max(abs(energy[:,-1]-a['initial'])-a['terminal_tolerance'])),
        'grid':max(0.,np.max(a['grid_lo']-grid),np.max(grid-a['grid_hi'])),
        'ramp':max(0.,np.max(abs(np.diff(np.r_[a['previous'],grid]))-a['ramp'])),
        'exclusivity':max(0.,np.max(np.minimum(c,d)))}
    cost = np.dot(grid,a['price']) + np.sum(a['wear'][:,None]*(c+d))
    return dict(valid=bool(np.all(np.isfinite(c)) and np.all(np.isfinite(d))
                           and max(violations.values()) <= DESIGN['A']['physical_tolerance']),
                cost=float(cost), residuals=violations)


def model(a, groups, kind='mixed', modes=None, symmetry=False):
    m = LinearModel()
    n,t = a['n'],a['t']
    p = a['power'][:,None]*a['availability']
    c = m.vars((n,t),hi=p,cost=a['wear'][:,None])
    d = m.vars((n,t),hi=p,cost=a['wear'][:,None])
    e = m.vars((n,t),lo=a['floor'],hi=a['capacity'][:,None])
    g = m.vars((t,),lo=a['grid_lo'],hi=a['grid_hi'],cost=a['price'])
    z = m.vars((len(groups),t),lo=modes if modes is not None else 0,
               hi=modes if modes is not None else 1,integer=kind!='lp' and modes is None)
    for k,group in enumerate(groups):
        lead=group[0]
        for i in group:
            for h in range(t):
                m.constraint([(c[i,h],1),(z[k,h],-p[i,h])],hi=0)
                m.constraint([(d[i,h],1),(z[k,h],p[i,h])],hi=p[i,h])
                terms=[(e[i,h],1),(c[i,h],-a['eta_c'][i]),(d[i,h],1/a['eta_d'][i])]
                rhs=a['initial'][i] if h==0 else 0
                if h: terms.append((e[i,h-1],-1))
                m.constraint(terms,rhs,rhs)
                if kind=='proportional' and i!=lead:
                    for v in [c,d]:
                        m.constraint([(v[i,h],a['capacity'][lead]),(v[lead,h],-a['capacity'][i])],0,0)
            target=a['initial'][i]
            eps=a['terminal_tolerance'][i]
            m.constraint([(e[i,-1],1)], target-eps,target+eps)
    for h in range(t):
        m.constraint([(g[h],1)]+[(c[i,h],-1) for i in range(n)]+[(d[i,h],1) for i in range(n)],
                     a['load'][h],a['load'][h])
        terms=[(g[h],1)]
        prev=a['previous'] if h==0 else 0
        if h: terms.append((g[h-1],-1))
        m.constraint(terms,prev-a['ramp'],prev+a['ramp'])
    if symmetry:
        # Only valid for fully interchangeable data. Order complete binary mode histories lexicographically.
        if a['cohort']!='interchangeable': raise ValueError('Nonexchangeable batteries')
        for i in range(1,n):
            terms=[]
            for h in range(t):
                weight=2**(t-1-h)
                terms.extend([(z[i-1,h],weight),(z[i,h],-weight)])
            m.constraint(terms,lo=0)
    return m,c,d


def lp_lower(m, y):
    """Evaluate a Lagrangian box lower bound for the full LP using its row multipliers."""
    y=np.asarray(y,dtype=np.longdouble)
    lo,hi=np.asarray(m.lhs),np.asarray(m.rhs)
    y[(y>0)&~np.isfinite(lo)] = 0
    y[(y<0)&~np.isfinite(hi)] = 0
    active=y!=0
    term=y[active]*np.where(y[active]>0,lo[active],hi[active])
    costs=np.asarray(m.cost,dtype=np.longdouble)
    transposed=m.A.T.astype(np.longdouble)
    residual=costs-transposed@y
    corners=np.where(residual>=0,m.lo,m.hi)
    value=np.sum(term)+np.sum(residual*corners)
    scale=1+np.sum(abs(term))+np.sum((abs(costs)+abs(transposed)@abs(y))
                                      *np.maximum(abs(np.array(m.lo)),abs(np.array(m.hi))))
    return float(value-1e-12*scale)


def refine(groups, c, d):
    """Split each group at its median, ordered by LP charge-minus-discharge at peak conflict."""
    result=[]
    for group in groups:
        if len(group)==1:
            result.append(group)
            continue
        order=group
        if c is not None:
            net=(c-d)[group]
            h=int(np.argmax(np.ptp(net,axis=0)))
            order=sorted(group,key=lambda i:(c[i,h]-d[i,h],i))
        mid=len(group)//2
        result.extend([order[:mid],order[mid:]])
    return result
