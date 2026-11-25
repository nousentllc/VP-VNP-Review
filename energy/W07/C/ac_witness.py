"""Interval existence test for an exact AC solution around a local candidate (Arb, 160 bits)."""
import numpy as np
from scipy.linalg import qr
from flint import arb,acb,arb_mat
from fractions import Fraction as F
from network import ball,upper


def prepare(g,point):
    n=g.n;ng=g.ng
    x=list(map(lambda a:F.from_float(float(a)),point))
    x[n+g.ref]=F(0);fixed={n+g.ref}
    for j,b in enumerate(g.gen):
        for k,lo,hi in ((2*n+j,b[9],b[8]),(2*n+ng+j,b[4],b[3])):
            if lo==hi:x[k]=lo/g.b;fixed.add(k)
    return x,[k for k in range(len(x)) if k not in fixed]


def evaluate(g,x,cols):
    n=g.n;ng=g.ng;v=[acb(x[i],x[n+i]) for i in range(n)]
    currents=[sum(y*v[j] for j,y in row.items()) for row in g.Y]
    net=[v[i]*currents[i].conjugate()+acb(ball(b[2]/g.b),ball(b[3]/g.b)) for i,b in enumerate(g.bus)]
    for j,i in enumerate(g.gb):net[i]-=acb(x[2*n+j],x[2*n+ng+j])
    mat=arb_mat(2*n,len(cols));pos={c:k for k,c in enumerate(cols)}
    def insert(i,col,z):
        if col in pos:mat[i,pos[col]]=z.real;mat[n+i,pos[col]]=z.imag
    for i in range(n):
        for j,y in g.Y[i].items():
            z=v[i]*y.conjugate();a=currents[i].conjugate() if i==j else acb(0)
            insert(i,j,a+z);insert(i,n+j,acb(0,1)*(a-z))
    for j,i in enumerate(g.gb):
        insert(i,2*n+j,acb(-1));insert(i,2*n+ng+j,acb(0,-1))
    f=arb_mat(2*n,1,[z.real for z in net]+[z.imag for z in net])
    return f,mat


def witness(g,point,selection=None):
    n,ng=g.n,g.ng
    q,eligible=prepare(g,point);x=[ball(v) for v in q]
    f,jac=evaluate(g,x,eligible)
    if selection is None:
        approximate=np.array(jac.tolist(),dtype=float)
        _,_,perm=qr(approximate,pivoting=True,mode='economic')
        selection=[eligible[k] for k in perm[:2*n]]
    assert len(set(selection))==2*n and set(selection)<=set(eligible)
    _,mid=evaluate(g,x,selection)
    # An approximate real inverse suffices; embed its rounded coefficients as exact dyadics.
    inv=np.linalg.inv(np.array(mid.tolist(),dtype=float))
    R=arb_mat(2*n,2*n,[ball(float(v)) for v in inv.ravel()])
    residual=R*f
    residual_norm=max(upper(abs(residual[k,0])) for k in range(2*n))
    radius=F(1,10**10)
    X=x.copy()
    for j in selection:X[j]+=arb(0,ball(radius))
    _,J=evaluate(g,X,selection)
    I=arb_mat(2*n,2*n); 
    for i in range(2*n):I[i,i]=1
    K=I-R*J
    norm=max(upper(sum(abs(K[i,j]) for j in range(2*n))) for i in range(2*n))
    assert residual_norm+norm*radius<radius and norm<1,('contraction',float(residual_norm),float(norm))
    # A fixed point has RF=0. ||I-RJ||<1 ensures R is nonsingular.
    V=[acb(X[i],X[n+i]) for i in range(n)]
    def between(y,lo,hi,name):
        assert y>=ball(lo) and y<=ball(hi), (name,str(y),str(lo),str(hi))
    for i,(v,b) in enumerate(zip(V,g.bus)):between(abs(v)**2,b[12]**2,b[11]**2,'voltage '+str(i))
    for k,((i,j,ff,ft,tf,tt),line) in enumerate(zip(g.edges,g.branch)):
        if line[5]>0:
            for u,cur in [(i,ff*V[i]+ft*V[j]),(j,tf*V[i]+tt*V[j])]:
                assert abs(V[u]*cur.conjugate())*ball(g.b)<=ball(line[5]),('thermal',k)
        between((V[i].arg()-V[j].arg())*180/arb.pi(),line[11],line[12],'angle '+str(k))
    assert X[n+g.ref].is_zero() and X[g.ref]>0
    cost=arb(0)
    for k,(gen,c) in enumerate(zip(g.gen,g.cost)):
        P=X[2*n+k]*ball(g.b);Q=X[2*n+ng+k]*ball(g.b)
        # Fixed boxes are set as exact input rationals in prepare(); conversion can widen non-dyadic bounds.
        if gen[8]!=gen[9]:between(P,gen[9],gen[8],'pg')
        if gen[3]!=gen[4]:between(Q,gen[4],gen[3],'qg')
        cost+=ball(c[0])*P**2+ball(c[1])*P+ball(c[2])
    return dict(U=upper(cost),selection=selection,radius=radius,residual_norm=residual_norm,lipschitz_norm=norm)
