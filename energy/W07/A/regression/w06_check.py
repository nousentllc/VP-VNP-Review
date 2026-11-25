"""Independent standard-library physical, dual and discrete-optimum replay."""
import argparse
import csv
import gzip
import hashlib
import json
import math
from collections import Counter, defaultdict
from fractions import Fraction as F
from pathlib import Path
from statistics import median


def load(p):
    data=p.read_bytes()
    return json.loads(gzip.decompress(data) if p.suffix==".gz" else data)


def physical(x,raw,fixed=None):
    state=x["initial"];last=0;cost=0;loss=0;levels=[]
    actions=raw["actions"]
    assert len(actions)==x["n"]
    for i,a in enumerate(actions):
        assert type(a) is int
        inflow=max(0,a);outflow=max(0,-a)
        assert inflow<=x["charge"][i] and outflow<=x["discharge"][i]
        assert abs(a-last)<=x["ramp"]
        force=x["force"][i]
        assert (force==0 or (a>=force if force>0 else a<=force))
        state+=a;assert x["floor"][i]<=state<=x["capacity"]
        delivered=(min(x["demand"][i],x["grid"][i]-5*inflow+4*outflow)
                   if fixed is None else fixed[i])
        imported=delivered+5*inflow-4*outflow
        assert 0<=imported<=x["grid"][i] and 0<=delivered<=x["demand"][i]
        levels.append(delivered);loss+=x["demand"][i]-delivered
        cost+=imported*x["price"][i]+x["wear"]*(5*inflow+4*outflow)
        last=a
    assert x["terminal"][0]<=state<=x["terminal"][1]
    cost-=4*x["credit"]*(state-x["initial"])
    have=dict(end=state,cost=cost,service=loss,served=levels)
    for k in have:
        if k in raw: assert have[k]==raw[k],(k,have[k],raw[k])
    return have


def dual(x,m,b,lp):
    # Independent direct coefficient expansion, without solver, matrix builder or numpy.
    e=list(map(F,lp["equality"])); u=list(map(F,lp["inequality"]))
    n=x["n"];cost=m=="cost"
    assert len(e)==2*n and len(u)==4*n and max(u)<=0
    bound=4*x["initial"]*x["credit"] if cost else 0
    for t in range(n):
        y,h=e[2*t:2*t+2];v,z,p,s=u[4*t:4*t+4]
        hnext=e[2*t+3] if t+1<n else 0
        rampnext=u[4*t+6]-u[4*t+7] if t+1<n else 0
        slew=p-s-rampnext
        C,D=x["charge"][t],x["discharge"][t];f=x["force"][t]
        shed=x["demand"][t]-b["served"][t]
        bound+=y*x["demand"][t]+(h*x["initial"] if t==0 else 0)+z*D+(p+s)*x["ramp"]
        soclo=max(x["floor"][t],x["terminal"][0] if t==n-1 else 0)
        sochi=x["terminal"][1] if t==n-1 else x["capacity"]
        factors=[
            ((5*x["wear"] if cost else 0)+5*y+h-v-slew,max(0,f),C),
            ((4*x["wear"] if cost else 0)-4*y-h-z+slew,max(0,-f),D),
            ((-4*x["credit"] if cost and t==n-1 else 0)-h+hnext,soclo,sochi),
            ((x["price"][t] if cost else 0)-y,0,x["grid"][t]),
            ((0 if cost else 1)-y,shed if cost else 0,shed if cost else x["demand"][t]),
            (C*v-D*z,0,1)]
        for r,l,h in factors: bound+=min(r*l,r*h)
    assert bound==F(lp["lower"])
    return bound


def backward(x,metric,baseline):
    # Cost-to-go computed backward on the full finite graph. No call to campaign DP.
    n=x["n"]; cap=x["capacity"];ramp=x["ramp"];M=max(x["charge"]+x["discharge"])
    value={(s,a):(-4*x["credit"]*(s-x["initial"]) if metric=="cost" else 0)
           for s in range(x["terminal"][0],x["terminal"][1]+1) for a in range(-M,M+1)}
    layers=[len(value)];arcs=0
    for t in reversed(range(n)):
        earlier={}
        for s in range(cap+1):
            # A choice of next state determines signed battery command uniquely.
            options=[]
            for sn in range(max(x["floor"][t],s-x["discharge"][t]),min(cap,s+x["charge"][t])+1):
                a=sn-s
                if (sn,a) not in value:continue
                f=x["force"][t]
                if (f>0 and a<f) or (f<0 and a>f):continue
                import_change=5*a if a>=0 else 4*a
                peak=x["grid"][t]-import_change
                delivered=baseline["served"][t] if metric=="cost" else min(x["demand"][t],peak)
                grid=delivered+import_change
                if not 0<=grid<=x["grid"][t] or not 0<=delivered<=x["demand"][t]:continue
                delta=(x["price"][t]*grid+x["wear"]*abs(import_change) if metric=="cost"
                       else x["demand"][t]-delivered)
                options.append((a,delta+value[(sn,a)]))
            for prev in range(-M,M+1):
                valid=[v for a,v in options if abs(a-prev)<=ramp]
                arcs+=len(valid)
                if valid: earlier[s,prev]=min(valid)
        value=earlier; layers.append(len(value))
    return value[x["initial"],0], layers, arcs


def coverage_guard(ids,records):
    expected={(x,m) for x in ids for m in ("service","cost")}
    keys=[(r["case"],r["objective"]) for r in records]
    assert len(keys)==len(expected) and set(keys)==expected


def audit(data,out):
    out.mkdir(parents=True,exist_ok=False)
    from model import PLAN,generate
    expected=[generate(i,h,g) for i in range(len(PLAN["seeds"])) for h in PLAN["horizons_h"] for g in PLAN["regimes"]]
    panel=load(data/"instances.json.gz")
    assert len(expected)==72 and panel==expected, "holdout schedule mismatch"
    cases={x["id"]:x for x in panel}
    shadows=load(data/"shadow.json.gz");controls=load(data/"controls.json")
    coverage_guard(cases,shadows)
    from model import controls as fixtures
    controls_x={x["id"]:x for _,_,x in fixtures()}
    assert len(controls)==8 and {r["case"] for r in controls}==set(controls_x)
    rows=[];mutations={};comparisons=Counter();proofs=[]
    mutant_done=False
    for r in shadows+controls:
        key=r["case"];m=r["objective"];ctl=key in controls_x
        x=controls_x[key] if ctl else cases[key]
        row=dict(case=key,objective=m,regime=x["regime"],hours=x["n"],closing=("fixed" if x["terminal"][0]==x["terminal"][1] else "floor"),
                 status=r["decision"],reason=r["reason"],control=ctl)
        if r["baseline"] is None:
            assert x["status"] in ("infeasible","missing")
            rows.append(row);continue
        b=physical(x,r["baseline"])
        upper=b[m]
        fixed=b["served"] if m=="cost" else None
        target=max(F(4 if m=="service" else 80),abs(upper)*F(3,100));assert F(r["target"])==target
        c=r["certificates"]
        feasible=physical(x,c["dp"],fixed);opt,layers,arcs=backward(x,m,b)
        assert feasible[m]==opt==r["best"]
        proofs.append(dict(case=key,objective=m,reachable_backward_states=layers,checked_arcs=arcs,optimum_native_units=opt))
        lower=dual(x,m,b,c["lp"])
        native=c["native"]
        if native["actions"] is not None:
            val=physical(x,native,fixed)[m]
            assert val>=opt
            if val==opt: comparisons["native_primal_equals_DP"]+=1
        if native["reported_bound"] is not None and abs(native["reported_bound"]-opt)<1e-6:comparisons["native_dual_matches_DP_to_1e-6"]+=1
        assert opt>=c["power"] and opt>=c["energy"] and opt>=lower and opt>=c["lattice"]
        assert r["decision"]==("demonstrated" if upper-opt>=target else "excluded")
        if ctl: assert upper-opt==r["known_improvement_native_units"]
        if not mutant_done and not ctl:
            bad=dict(r["baseline"],actions=[x["capacity"]+7]+r["baseline"]["actions"][1:])
            try: physical(x,bad)
            except AssertionError: mutations["infeasible_SOC_witness_rejected"]=True
            altered=dict(c["lp"],inequality=["1"]+c["lp"]["inequality"][1:])
            try: dual(x,m,b,altered)
            except AssertionError:mutations["wrong_inequality_sign_rejected"]=True
            mutant_done=True
        stages=[("power",F(c["power"])),("energy",F(c["energy"])),("lp",lower),("lattice",F(c["lattice"])),("dp",F(opt))]
        best_l=None
        row.update(baseline_physical=upper/4,direct_native_status=native["status"],dp_optimum=opt/4,
                   target_physical=float(target/4),actual_opportunity=(upper-opt)/4,
                   threshold_abs_excluded=(upper-opt < (4 if m=="service" else 80)),
                   threshold_relative_excluded=(upper-opt < abs(upper)*F(3,100)),
                   strict_equality=(upper-opt==target),stop_tier="unexcluded",
                   case_weight="control" if ctl else "1/72")
        for name,val in stages:
            best_l=val if best_l is None else max(val,best_l)
            ceiling=upper-best_l
            row[name+"_lower"]=str(best_l/4);row[name+"_ceiling"]=str(ceiling/4)
            row[name+"_excludes"]=ceiling<target
            if ceiling<target and row["stop_tier"]=="unexcluded":row["stop_tier"]=name
        rows.append(row)
    try: coverage_guard(cases,shadows[1:])
    except AssertionError: mutations["missing_panel_row_rejected"]=True
    assert len(mutations)==3
    with (out/"cases.csv").open("w") as f:
        keys=list(dict.fromkeys(k for row in rows for k in row))
        w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(rows)
    checks=dict(case_objectives=len(shadows),controls=len(controls),eligible=sum(r["status"]!="invalid" for r in rows if not r["control"]),
                verified_comparisons_including_controls=dict(comparisons),mutations=mutations,
                independent_backward_arcs=sum(r["checked_arcs"] for r in proofs))
    (out/"verification.json").write_text(json.dumps(checks,indent=2)+"\n")
    (out/"bellman_check.json.gz").write_bytes(gzip.compress(json.dumps(proofs,separators=(",",":")).encode(),mtime=0))
    timing=load(data/"timed.json.gz")
    assert len(timing)==len(shadows)*3*3
    shadow={(r["case"],r["objective"]):r for r in shadows}
    seen=set(); paired=defaultdict(dict); modes=defaultdict(list); percase=defaultdict(list)
    for r in timing:
        k=(r["case"],r["objective"]);s=shadow[k]; arm=r["arm"];rep=r["repeat"]
        assert (*k,arm,rep) not in seen
        seen.add((*k,arm,rep)); x=cases[k[0]]
        if s["baseline"] is not None:
            assert r["baseline"]==s["baseline"]
            if arm in ("dp","staged"): assert r["decision"]==s["decision"]
            if r["lower"] is not None: assert F(r["lower"])<=s["best"]
            cert=r["certificates"]
            if "lp" in cert:dual(x,k[1],r["baseline"],cert["lp"])
            if "native" in cert and cert["native"]["actions"] is not None:
                physical(x,cert["native"],r["baseline"]["served"] if k[1]=="cost" else None)
        else: assert r["decision"]=="invalid"
        paired[(*k,rep)][arm]=r["ipc_wall_s"]
        percase[(*k,arm)].append(r["ipc_wall_s"])
        modes[(k[1],arm)].append(r)
    timing_stats=[]
    for (m,arm),rs in modes.items():
        good=[r for r in rs if r["decision"]!="invalid"]
        t=[r["ipc_wall_s"] for r in good]; t.sort()
        timing_stats.append(dict(objective=m,arm=arm,all_attempts=len(rs),eligible_attempts=len(t),median_ms=median(t)*1000,
                                 p95_ms=t[math.ceil(.95*len(t))-1]*1000,eligible_total_s=sum(t),
                                 full_total_s=sum(r["ipc_wall_s"] for r in rs),
                                 dispatcher_deadline_misses=sum(r["ipc_wall_s"]>.5 for r in rs),
                                 max_worker_peak_MiB=max(r["process_max_rss_bytes"] for r in rs)/2**20))
    def pairs(m,arm):
        out=[]
        for (case,metric),s in shadow.items():
            if metric==m and s["baseline"]:
                base=median(percase[(case,metric,arm)]);stage=median(percase[(case,metric,"staged")])
                out.append((stage-base)*1000)
        return dict(n=len(out),stage_faster=sum(x<0 for x in out),stage_slower=sum(x>0 for x in out),median_paired_ms=median(out))
    results={}
    for metric in ["service","cost"]:
        rr=[r for r in rows if r["objective"]==metric and not r["control"]]; good=[r for r in rr if r["status"]!="invalid"]
        excluded=sum(r["status"]=="excluded" for r in rr)
        results[metric]=dict(all=len(rr),eligible=len(good),excluded=excluded,demonstrated=len(good)-excluded,
                             invalid=len(rr)-len(good),by_first_stop=dict(Counter(r["stop_tier"] for r in good)),
                             exact_zero=sum(r["actual_opportunity"]==0 for r in good),
                             absolute_only=sum(r["threshold_abs_excluded"] for r in good),
                             relative_only=sum(r["threshold_relative_excluded"] for r in good),
                             paired_stage_minus_native=pairs(metric,"native"),paired_stage_minus_dp=pairs(metric,"dp"),
                             regimes={g:dict(Counter(r["status"] for r in rr if r["regime"]==g)) for g in sorted({r["regime"] for r in rr})})
    (out/"summary.json").write_text(json.dumps(dict(coverage=results,timing=timing_stats),indent=2)+"\n")
    print(json.dumps(checks))


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--data",type=Path,required=True);p.add_argument("--out",type=Path,required=True)
    args=p.parse_args();audit(args.data,args.out)
