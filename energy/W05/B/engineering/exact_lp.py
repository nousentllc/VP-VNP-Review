"""Find an LP vertex numerically, reconstruct it on rational active rows, check the full LP bounds."""
from fractions import Fraction as F
import numpy as np
import scipy.linalg as la
from scipy.optimize import linprog
import sympy as sp
from model import zeros

def support(v,cap):
    return sum((max(F(0),z)*u for z,u in zip(v,cap)),F(0))

def solve(c,A,b,E,d,cap):
    x=linprog(np.asarray(c,float),A_ub=np.asarray(A,float),b_ub=np.asarray(b,float),
              A_eq=np.asarray(E,float) if len(d) else None,b_eq=np.asarray(d,float) if len(d) else None,
              bounds=[(0,float(u)) for u in cap],method='highs-ds')
    if not x.success:return dict(status=x.message,code=x.status)
    frac=lambda v:F(float(v)).limit_denominator(1000000)
    mu=np.array([min(F(0),frac(v)) for v in x.ineqlin.marginals],dtype=object)
    nu=np.array([frac(v) for v in x.eqlin.marginals],dtype=object)
    residual=c-mu@A-(nu@E if len(d) else 0)
    lower=mu@b+(nu@d if len(d) else 0)-support(-residual,cap)
    z=np.array([frac(t) for t in x.x],dtype=object)
    def valid(y):
        return all(y>=0) and all(y<=cap) and all(A@y<=b) and (not len(d) or all(E@y==d))
    if not valid(z):
        n=len(c);I=zeros((n,n));np.fill_diagonal(I,F(1))
        rows=np.vstack((E,A,I,I));rhs=np.r_[d,b,np.zeros(n,int),cap]
        active=np.flatnonzero(abs(np.asarray(rows,float)@x.x-np.asarray(rhs,float))<1e-7)
        _,_,ix=la.qr(np.asarray(rows[active],float).T,pivoting=True,mode='economic')
        use=active[ix[:n]]
        try:
            raw=sp.Matrix(rows[use].tolist()).inv()*sp.Matrix(rhs[use].tolist())
            z=np.array([F(int(t.p),int(t.q)) for t in raw],dtype=object)
        except (ValueError,ZeroDivisionError):return dict(code=-2,status='rational basis failed',lower=lower)
    if not valid(z):return dict(code=-3,status='rational point failed original checks',lower=lower)
    upper=c@z;assert lower<=upper
    return dict(code=0,status=x.message,x=z,U=upper,L=lower,mu=mu,nu=nu)
