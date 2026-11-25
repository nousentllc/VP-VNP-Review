"""Exploratory clique PSD outer separation using exact rational complex test vectors."""
import sys,time,hashlib
from fractions import Fraction as F
from pathlib import Path
import numpy as np
from flint import arb
from network import Grid,ball,lower,upper
from ac_bound import Outer,quant
from linear import read,write
HERE=Path(__file__).resolve().parent


def extend(h):
    g=h.g
    neighbors={i:set() for i in range(g.n)}
    for i,j in h.pairs:neighbors[i].add(j);neighbors[j].add(i)
    candidates=[]
    while neighbors:
        p=min(neighbors,key=lambda i:(len(neighbors[i]),i));adj=neighbors.pop(p);cl=frozenset(adj|{p});candidates.append(cl)
        for i in adj:neighbors[i].discard(p);neighbors[i].update(adj-{i})
    cliques=[sorted(a) for a in candidates if len(a)>=3 and not any(a<b for b in candidates)]
    for cl in cliques:
        for k,i in enumerate(cl):
            for j in cl[k+1:]:
                if (i,j) not in h.pairs:
                    M=g.bus[i][11]*g.bus[j][11]
                    h.pairs[i,j]=(h.lp.var(f'fill_re{i}_{j}',-M,M),h.lp.var(f'fill_im{i}_{j}',-M,M))
    for (i,j,*_),br in zip(g.edges,g.branch):
        l,u=br[11:13]
        if -90<l<=u<90:
            re,im=h.pairs[tuple(sorted((i,j)))];s=1 if i<j else -1
            lb=lower((ball(l)*arb.pi()/180).tan());ub=upper((ball(u)*arb.pi()/180).tan())
            h.lp.row('pos_real',{re:1},0,None)
            h.lp.row('angle_lower',{im:s,re:-lb},0,None)
            h.lp.row('angle_upper',{im:s,re:-ub},None,0)
    return cliques


def psd(h,cl,z):
    co={}
    for k,(i,(a,b)) in enumerate(zip(cl,z)):
        co[h.w[i]]=a*a+b*b
        for j,(c,d) in zip(cl[k+1:],z[k+1:]):
            R,I=h.pairs[i,j]
            co[R]=2*(a*c+b*d);co[I]=-2*(a*d-b*c)
    h.lp.row('clique_psd',co,0,None)


def sep(h,cliques,x):
    rows=[]
    for cl in cliques:
        m=np.diag([complex(x[h.w[i]]) for i in cl])
        for k,i in enumerate(cl):
            for l,j in enumerate(cl[k+1:],k+1):
                r,b=h.pairs[i,j];m[k,l]=complex(x[r],x[b]);m[l,k]=m[k,l].conjugate()
        ev,E=np.linalg.eigh(m)
        for k,lam in enumerate(ev):
            if lam>=-1e-7:break
            v=[(quant(a.real),quant(a.imag)) for a in E[:,k]]
            rows.append((cl,v))
    return rows


def load_primary(path,source):
    g=Grid(path);h=Outer(g);r=read(source/'summary.json');raw=read(source/'witnesses.json.gz')
    for kind,obj,*vv in raw['cuts']:
        h.cut(kind,tuple(obj) if isinstance(obj,list) else obj,*map(F,vv))
    return h,r,extend(h)


def run(path,source,d):
    t=time.perf_counter();h,r,cliques=load_primary(path,source)
    U=F(r['U']);L=F(r['L']);trace=[];rounds=[];pending=[]
    for k in range(24):
        inserted=[];edge_start=len(h.cuts)
        if k:
            h.refine(x)
            for cl,vec in pending:
                psd(h,cl,vec);inserted.append([cl,[[str(a),str(b)] for a,b in vec]])
        solver,x,y=h.lp.optimize();l=h.lp.dual(y);assert l<=U;L=max(l,L)
        rounds.append(dict(added_edge_cuts=h.cuts[edge_start:],psd=inserted,dual=y))
        trace.append(dict(round=k,nrows=len(h.lp.rows),psd_cuts=len(inserted),L=l,**solver))
        if L>F(99,100)*U:break
        pending=sep(h,cliques,x)
    write(d/'proof.json.gz',rounds)
    write(d/'summary.json',dict(case=path.name,U=U,L=L,relative_pct=float(100*(U-L)/U),excluded=L>F(99,100)*U,
         largest_clique=max(map(len,cliques)),cliques=len(cliques),trace=trace,wall_s=time.perf_counter()-t))
    print(path.stem,float(100*(U-L)/U),len(trace),flush=True)


def audit(path,source,d):
    h,r,cliques=load_primary(path,source);s=read(d/'summary.json');L=F(r['L']);U=F(r['U'])
    for proof,row in zip(read(d/'proof.json.gz'),s['trace'],strict=True):
        for kind,obj,*v in proof['added_edge_cuts']:h.cut(kind,tuple(obj) if isinstance(obj,list) else obj,*map(F,v))
        for cl,z in proof['psd']:
            assert cl in cliques;psd(h,cl,[(F(a),F(b)) for a,b in z])
        l=h.lp.dual(list(map(F,proof['dual'])));assert l==F(row['L']) and l<=U;L=max(l,L)
    assert L==F(s['L'])
    return s['excluded']


if __name__=='__main__':
    action,primary,out=sys.argv[1],Path(sys.argv[2]),Path(sys.argv[3])
    for p in sorted((HERE/'inputs').glob('*__api.m')):
        source=primary/p.stem;dest=out/p.stem
        if action=='run':
            if (dest/'summary.json').exists():raise FileExistsError(dest)
            run(p,source,dest)
        else:print(p.stem,audit(p,source,dest))
