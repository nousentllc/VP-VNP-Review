"""Run frozen instances, offline all-tier audit and rotated timed decision arms."""
import argparse
import gzip
import hashlib
import json
import math
import os
import platform
import resource
import subprocess
import sys
import time
import warnings
from datetime import datetime, timezone
from fractions import Fraction as F
from pathlib import Path

for var in ("OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS","VECLIB_MAXIMUM_THREADS"):
    os.environ[var]="1"
from model import PLAN,ROOT,baseline,controls,generate,optimize,threshold,witness
import bounds


def dump(path,obj):
    data=(json.dumps(obj,separators=(",",":"),sort_keys=True)+"\n").encode()
    path.write_bytes(gzip.compress(data,mtime=0) if path.suffix==".gz" else data)


def when(): return datetime.now(timezone.utc).isoformat()
def rss_bytes():
    v=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(v if sys.platform=="darwin" else v*1024)


def trial(x,metric,arm):
    start=time.perf_counter()
    stages={}
    def run_stage(name,fn,*args):
        tic=time.perf_counter()
        result=fn(*args)
        stages[name]=time.perf_counter()-tic
        return result
    w,err=run_stage("baseline_build_and_verify",baseline,x)
    record=dict(case=x["id"],objective=metric,arm=arm,baseline=w,reason=err,stages_s=stages,
                decision="invalid",lower=None,best=None,certificates={},clock_target_s=.5)
    def finish():
        elapsed=time.perf_counter()-start
        record.update(wall_s=elapsed,within_deadline=elapsed<=.5,process_max_rss_bytes=rss_bytes())
        return record
    if w is None: return finish()
    upper=w[metric]; target=threshold(metric,upper); best=upper; lower=None
    record.update(baseline_value=upper,target=str(target),best=best,decision="unresolved")
    fixed=w["served"] if metric=="cost" else None
    def spend(l):
        nonlocal lower
        l=F(l);lower=max(lower,l) if lower is not None else l
        if lower>best: raise ValueError((x["id"],metric,lower,best))
        record["lower"]=str(lower)
        if upper-lower<target: record["decision"]="excluded"
        return record["decision"]=="excluded"
    if arm in ("staged","shadow"):
        # Separate the cheap power-only path, without paying for the energy tier.
        cheap=run_stage("power",power,x,metric,w)
        record["certificates"]["power"]=cheap
        if spend(cheap) and arm=="staged": return finish()
        simple,energy=run_stage("energy",bounds.analytic,x,metric,w)
        assert cheap==simple
        record["certificates"]["energy"]=energy
        if spend(energy) and arm=="staged": return finish()
        lp=run_stage("lp_build_solve_rational_check",bounds.lp_bound,x,metric,w)
        record["certificates"]["lp"]=lp
        if lp["success"]:
            if spend(lp["lower"]) and arm=="staged": return finish()
            def round_lattice():
                spacing=(math.gcd(*x["price"],5*x["wear"],4*x["wear"],4*x["credit"]) or 1) if metric=="cost" else 1
                return spacing*math.ceil(lower/spacing)
            lattice=run_stage("integer_objective_lattice",round_lattice)
            record["certificates"]["lattice"]=lattice
            if spend(lattice) and arm=="staged": return finish()
    if arm in ("native","shadow"):
        native=run_stage("milp_build_and_solve",bounds.native,x,metric,w)
        record["certificates"]["native"]=native
        alternative=run_stage("milp_primal_check",witness,x,native["actions"],fixed)
        if alternative is not None:
            best=min(best,alternative[metric]);record["best"]=best
            if upper-best>=target: record["decision"]="demonstrated"
        if arm=="native":
            # Native floating proof is a comparator, never an independent exact lower certificate.
            b=native["reported_bound"]
            record["native_would_exclude"]=b is not None and upper-b<float(target)
            return finish()
    if arm in ("staged","dp","shadow"):
        def exact():
            a=optimize(x,0,x["n"],x["initial"],0,x["terminal"],fixed=fixed)
            wp=witness(x,a,fixed)
            if wp is None: raise ValueError("exact oracle failed")
            return wp
        alternate=run_stage("discrete_search_and_verify",exact)
        exact_opt=alternate[metric]; record["certificates"]["dp"]=alternate; best=min(best,exact_opt);record["best"]=best
        spend(exact_opt)
        record["decision"]="demonstrated" if upper-best>=target else "excluded"
    return finish()


def power(x,metric,w):
    if metric=="service": return sum(max(0,q-g-4*d) for q,g,d in zip(x["demand"],x["grid"],x["discharge"]))
    return (sum(p*(max(0,q-4*d) if p>=0 else min(g,q+5*c))
                for p,q,d,g,c in zip(x["price"],w["served"],x["discharge"],x["grid"],x["charge"]))
            -4*x["credit"]*(x["terminal"][1]-x["initial"]))


def worker():
    warnings.filterwarnings("ignore",message="Unrecognized options detected")
    warnings.filterwarnings("ignore",message="Unrecognized options")
    # Public, constructed fixture warms the relevant native solver; separate from all holdouts.
    _,_,fixture=controls()[2]
    trial(fixture,"service","shadow")
    print("ready",flush=True)
    for line in sys.stdin:
        x,metric,arm=json.loads(line)
        r=trial(x,metric,arm)
        print(json.dumps(r,separators=(",",":")),flush=True)


def run(out):
    start=time.perf_counter()
    out.mkdir(parents=True,exist_ok=False)
    freeze=json.loads((ROOT/"protocol/freeze.json").read_text())
    for name,h in freeze["sha256"].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==h,name
    panel=[generate(i,h,r) for i in range(len(PLAN["seeds"])) for h in PLAN["horizons_h"] for r in PLAN["regimes"]]
    assert len({x["id"] for x in panel})==72
    dump(out/"instances.json.gz",panel)
    records=[];timings=[]
    def launch():
        before=time.perf_counter()
        p=subprocess.Popen([sys.executable,str(ROOT/"campaign.py"),"--worker"],stdin=subprocess.PIPE,
                           stdout=subprocess.PIPE,text=True,bufsize=1)
        assert p.stdout.readline().strip()=="ready"
        return p,time.perf_counter()-before
    arms=["staged","native","dp"]
    pool={}; startup={}
    for name in [*arms,"shadow"]: pool[name],startup[name]=launch()
    def request(x,metric,arm):
        tic=time.perf_counter();w=pool[arm]
        w.stdin.write(json.dumps([x,metric,arm])+"\n");w.stdin.flush()
        line=w.stdout.readline()
        if not line: raise RuntimeError((arm,x["id"],w.poll()))
        result=json.loads(line)
        result["ipc_wall_s"]=time.perf_counter()-tic
        return result
    try:
        for idx,x in enumerate(panel):
            for j,metric in enumerate(["service","cost"]):
                for rep in range(3):
                    for step in range(3):
                        arm=arms[(idx+j+rep+step)%3]
                        r=request(x,metric,arm);r["repeat"]=rep
                        timings.append(r)
                records.append(request(x,metric,"shadow"))
        ctrls=[]
        for metric,known,x in controls():
            r=request(x,metric,"shadow"); r["known_improvement_native_units"]=known if metric=="service" else 4*known
            ctrls.append(r)
    finally:
        for w in pool.values():
            w.stdin.close()
        for w in pool.values(): w.wait()
    dump(out/"timed.json.gz",timings)
    dump(out/"shadow.json.gz",records)
    dump(out/"controls.json",ctrls)
    import scipy,numpy
    dump(out/"run.json",dict(utc=when(),elapsed_s=time.perf_counter()-start,
         worker_launch_warmup_s=startup,driver_max_rss_bytes=rss_bytes(),scipy=scipy.__version__,
         numpy=numpy.__version__,python=sys.version,platform=platform.platform(),node_threads=1,
         sys_executable=Path(sys.executable).name))


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--out",type=Path);p.add_argument("--worker",action="store_true")
    options=p.parse_args()
    if options.worker: worker()
    else: run(options.out)
