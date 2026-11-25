"""Extensive-form decision-node binary MILP, independent of Bellman recursion."""
def solve(table):
    from itertools import product
    import numpy as np
    from scipy.optimize import Bounds, LinearConstraint, milp
    from scipy.sparse import coo_array
    nodes=[''.join(b) for t in range(6) for b in product('01',repeat=t)]
    pos={h:5*i for i,h in enumerate(nodes)}
    n=5*len(pos); coeff=np.zeros(n); lo=np.zeros(n); hi=np.full(n,np.inf)
    integer=np.zeros(n); rows=[]; cols=[]; values=[]; left=[]; right=[]; mass={'':1.0}
    def row(items,lb,ub):
        for idx,v in items:
            rows.append(len(left));cols.append(idx);values.append(v)
        left.append(lb);right.append(ub)
    for h in nodes:
        t=len(h); z=int(h[-1]) if h else 0; d=table[t][z]; i=pos[h]
        # charge, discharge, ending SOC, ordinary import, firm backup
        hi[i:i+4]=[1,1,4,d['cap']]; integer[i:i+2]=1
        coeff[i:i+5]=mass[h]*np.array([d['wear'],d['wear'],0,d['price'],d['backup']])
        prev=pos[h[:-1]] if t else None
        row([(i,1),(i+1,1)],0,1)
        row([(i+2,1),(i,-1),(i+1,1)]+([(prev+2,-1)] if t else []),0 if t else 2,0 if t else 2)
        row([(i,1),(i+1,-1)]+([(prev,-1),(prev+1,1)] if t else []),-1,1)
        row([(i+3,1),(i+4,1),(i,-5),(i+1,4)],d['demand'],d['demand'])
        if t==5:
            row([(i+2,1)],2,2)
        else:
            mass[h+'1']=mass[h]*d['q']/8;mass[h+'0']=mass[h]*(8-d['q'])/8
    matrix=coo_array((values,(rows,cols)),shape=(len(left),n)).tocsc()
    result=milp(coeff,integrality=integer,bounds=Bounds(lo,hi),
                constraints=LinearConstraint(matrix,left,right),
                options={'mip_rel_gap':0.0,'time_limit':60})
    if not result.success:
        raise RuntimeError(str(result.message))
    return {'objective':result.fun,'dual_float':result.mip_dual_bound,'mip_nodes':result.mip_node_count,
            'status':result.message,'integer_residual':max(abs(result.x[i+j]-round(result.x[i+j])) for i in pos.values() for j in (0,1)),
            'policy':{h:round(result.x[i])-round(result.x[i+1]) for h,i in pos.items()}}
