"""Sparse derivative and regularized KKT diagnostics outside the timed algorithm."""
import time
import numpy as np
import casadi as ca
from scipy import sparse as sp
from scipy.sparse.csgraph import reverse_cuthill_mckee
from scipy.sparse.linalg import splu, onenormest, LinearOperator

def symbolic(a):
    """Counts exact structural lower-triangular factor nonzeros via elimination-tree reach."""
    graph=a.astype(bool).astype(np.int8).tocsc()
    perm=reverse_cuthill_mckee(graph,symmetric_mode=True)
    g=graph[perm,:][:,perm].tocsc()
    n=g.shape[0];parent=np.full(n,-1);seen=np.full(n,-1);count=n
    for j in range(n):
        for k in g.indices[g.indptr[j]:g.indptr[j+1]]:
            if k>=j:continue
            while k!=-1 and k<j and seen[k]!=j:
                count+=1;seen[k]=j
                if parent[k]==-1:parent[k]=j
                k=parent[k]
    return int(count),perm

def probe(x,g,f,result):
    J=ca.jacobian(g,x);lam=ca.SX.sym('mult',g.numel())
    H=ca.hessian(f+ca.dot(lam,g),x)[0]
    fn=ca.Function('structure',[x,lam],[J,H])
    j,h=map(lambda z:z.sparse().tocsc(),fn(result['x'],result['lam_g']))
    S=j.copy();S.data[:]=1;P=h.copy();P.data[:]=1
    n,m=x.numel(),g.numel()
    graph=sp.bmat([[P+sp.eye(n),S.T],[S,sp.eye(m)]],format='csc')
    count,perm=symbolic(graph)
    k=sp.bmat([[h+1e-6*sp.eye(n),j.T],[j,-1e-6*sp.eye(m)]],format='csc')
    details=dict(jacobian_nnz=j.nnz,hessian_nnz=h.nnz,kkt_order=n+m,graph_nnz=graph.nnz,
                 rcm_factor_lower_nnz=count,added_lower_fill=count-(graph.nnz+n+m)//2)
    patterns=dict(jrow=j.indices,jptr=j.indptr,hrow=h.indices,hptr=h.indptr,rcm=perm)
    try:
        orig=time.perf_counter();fac=splu(k,permc_spec='COLAMD');details['proxy_factor_s']=time.perf_counter()-orig
        inv=LinearOperator(k.shape,matvec=fac.solve,rmatvec=lambda a:fac.solve(a,'T'),dtype=float)
        np.random.seed(1731)
        details['condition_1_est']=float(np.asarray(abs(k).sum(0)).max()*onenormest(inv))
    except (RuntimeError,ValueError) as exc:details['proxy_error']=str(exc)
    return details,patterns
