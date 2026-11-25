"""Power/ramp bounds, finite-box LP duals, and unrestricted native MILP."""
from fractions import Fraction as F
from time import perf_counter

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, linprog, milp


def analytic(x,metric,w):
    n=x["n"]; cap=x["capacity"]; lo,hi=x["terminal"]; start=x["initial"]
    # Highest discharge at an hour with only the converter and slew envelope relaxed.
    up=[]; down=[]
    cprev=dprev=0
    for t in range(n):
        cprev=min(x["charge"][t],cprev+x["ramp"])
        dprev=min(x["discharge"][t],dprev+x["ramp"])
        up.append(cprev); down.append(dprev)
    if metric=="service":
        simple=[max(0,x["demand"][t]-x["grid"][t]-4*x["discharge"][t]) for t in range(n)]
        point=[max(0,x["demand"][t]-x["grid"][t]-4*down[t]) for t in range(n)]
        # Any disjoint intervals may be summed. A full-horizon bound exploits initial and terminal SOC.
        dp=[0]
        for end in range(1,n+1):
            ans=dp[-1]+point[end-1]
            for k in range(end):
                s_upper=start if k==0 else min(cap,start+sum(up[:k]))
                s_lower=max(x["floor"][end-1],lo-sum(up[end:]))
                deficit=sum(x["demand"][k:end])-sum(x["grid"][k:end])-4*(s_upper-s_lower)
                ans=max(ans,dp[k]+deficit)
            dp.append(ans)
        return sum(simple),max(sum(simple),dp[-1])
    q=w["served"];p=x["price"]
    terminal_floor=-4*x["credit"]*(hi-start)
    def gridbox(d,c):
        gl=[max(0,q[t]-4*d[t]) for t in range(n)]
        gu=[min(x["grid"][t],q[t]+5*c[t]) for t in range(n)]
        return gl,gu
    gl,gu=gridbox(x["discharge"],x["charge"])
    naive=terminal_floor+sum(v*(low if v>=0 else high) for v,low,high in zip(p,gl,gu))
    gl,gu=gridbox(down,up)
    # Enumerate every possible terminal SOC and retain the smallest safe bound.
    floors=[]
    for closing in range(lo,hi+1):
        # Net imported energy equals served + 4 * SOC change + total charge blocks.
        demand=sum(q)+4*(closing-start)+max(0,closing-start)
        g=[high if price<0 else low for price,low,high in zip(p,gl,gu)]
        required=max(0,demand-sum(g))
        for i in sorted(range(n),key=p.__getitem__):
            increase=min(required,gu[i]-g[i]);g[i]+=increase;required-=increase
        if required: continue
        min_wear=x["wear"]*(5*max(0,closing-start)+4*max(0,start-closing))
        floors.append(sum(price*k for price,k in zip(p,g))+min_wear-4*x["credit"]*(closing-start))
    if not floors: raise ValueError("import boxes exclude feasible baseline")
    return naive,max(naive,min(floors))


def matrix(x,metric,w):
    n=x["n"]; N=6*n
    eq=[];ineq=[]; eb=[];ib=[]; lb=[];ub=[];c=[]
    def row(items):
        v=np.zeros(N,dtype=int)
        for j,a in items: v[j]+=a
        return v
    for t in range(n):
        C,D,S,G,H,Z=range(6*t,6*t+6)
        eq.append(row([(G,1),(H,1),(C,-5),(D,4)])); eb.append(x["demand"][t])
        entries=[(S,1),(C,-1),(D,1)]
        if t: entries.append((S-6,-1))
        eq.append(row(entries));eb.append(0 if t else x["initial"])
        ineq.append(row([(C,1),(Z,-x["charge"][t]) ]));ib.append(0)
        ineq.append(row([(D,1),(Z,x["discharge"][t]) ]));ib.append(x["discharge"][t])
        slew=[(C,1),(D,-1)]
        if t: slew.extend([(C-6,-1),(D-6,1)])
        r=row(slew)
        ineq.extend([r,-r]);ib.extend([x["ramp"]]*2)
        loss=x["demand"][t]-w["served"][t]
        lb.extend([max(0,x["force"][t]),max(0,-x["force"][t]),
                   max(x["floor"][t],x["terminal"][0] if t==n-1 else 0),0,
                   loss if metric=="cost" else 0,0])
        ub.extend([x["charge"][t],x["discharge"][t],x["terminal"][1] if t==n-1 else x["capacity"],
                   x["grid"][t],loss if metric=="cost" else x["demand"][t],1])
        c.extend([5*x["wear"],4*x["wear"],-4*x["credit"] if t==n-1 else 0,x["price"][t],0,0]
                 if metric=="cost" else [0,0,0,0,1,0])
    return dict(c=np.array(c),K=4*x["credit"]*x["initial"] if metric=="cost" else 0,
                eq=np.array(eq),eb=np.array(eb),G=np.array(ineq),gb=np.array(ib),
                lb=np.array(lb),ub=np.array(ub))


def rational(x): return str(F(float(x)).limit_denominator(1_000_000))


def exact_dual(m,y,mu):
    y=[F(v) for v in y];mu=[F(v) for v in mu]
    if len(y)!=len(m["eq"]) or len(mu)!=len(m["G"]) or any(v>0 for v in mu):
        raise ValueError("bad dual dimensions/sign")
    residual=[F(int(v)) for v in m["c"]]
    bound=F(m["K"])
    for vals,rows,b in [(y,m["eq"],m["eb"]),(mu,m["G"],m["gb"])]:
        for v,r,rhs in zip(vals,rows,b):
            if not v: continue
            bound+=v*int(rhs)
            for i in np.flatnonzero(r): residual[i]-=v*int(r[i])
    for a,l,h in zip(residual,m["lb"],m["ub"]): bound+=a*int(l if a>=0 else h)
    return bound


def lp_bound(x,metric,w):
    m=matrix(x,metric,w)
    res=linprog(m["c"],A_ub=m["G"],b_ub=m["gb"],A_eq=m["eq"],b_eq=m["eb"],
                bounds=list(zip(m["lb"],m["ub"])),method="highs",options={"threads":1,"time_limit":2.0})
    if not res.success: return dict(success=False,message=res.message)
    y=list(map(rational,res.eqlin.marginals));mu=[rational(min(v,0.0)) for v in res.ineqlin.marginals]
    l=exact_dual(m,y,mu)
    return dict(success=True,lower=str(l),numeric=res.fun+m["K"],equality=y,inequality=mu)


def native(x,metric,w):
    m=matrix(x,metric,w)
    integrality=np.zeros(len(m["c"]))
    # c,d and binary converter mode are integral. Others are determined; in the service
    # objective integer metering is explicitly enforced on the shed variables.
    integrality[0::6]=1;integrality[1::6]=1;integrality[4::6]=1;integrality[5::6]=1
    res=milp(m["c"],integrality=integrality,bounds=Bounds(m["lb"],m["ub"]),constraints=[
        LinearConstraint(m["eq"],m["eb"],m["eb"]),LinearConstraint(m["G"],-np.inf,m["gb"])],
        options={"threads":1,"time_limit":2.0,"mip_rel_gap":0.0,"presolve":True})
    lower=getattr(res,"mip_dual_bound",None)
    return dict(status=int(res.status),message=res.message,reported_bound=None if lower is None else lower+m["K"],
                reported_objective=None if res.fun is None else res.fun+m["K"],
                nodes=getattr(res,"mip_node_count",None),
                actions=None if res.x is None else [int(round(a-b)) for a,b in zip(res.x[::6],res.x[1::6])])
