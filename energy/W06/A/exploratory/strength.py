import argparse
import csv
import gzip
import json
import sys
import time
from collections import Counter
from fractions import Fraction
from hashlib import sha256
from pathlib import Path
from statistics import median

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from model import optimize,witness
from check import load,physical,backward


def compare(data,out):
    out.mkdir(parents=True,exist_ok=False)
    cases={x["id"]:x for x in load(data/"instances.json.gz")}
    rows=[]; raw=[];start=time.perf_counter()
    for row in load(data/"shadow.json.gz"):
        x=cases[row["case"]];m=row["objective"];b=row["baseline"]
        rr=dict(case=x["id"],objective=m,regime=x["regime"])
        if b is None:
            rows.append(dict(rr,status="invalid"));continue
        before=time.perf_counter()
        fixed=b["served"] if m=="cost" else None
        a=b["actions"][:]
        for offset in [0,4]:
            edges=sorted({0,x["n"],*range(offset,x["n"],8)})
            for l,h in zip(edges,edges[1:]):
                first=x["initial"]+sum(a[:l]);end=x["initial"]+sum(a[:h])
                action=optimize(x,l,h,first,a[l-1] if l else 0,
                                [end,end] if h<x["n"] else x["terminal"],
                                a[h] if h<x["n"] else None,fixed)
                assert action is not None
                a[l:h]=action
        alt=witness(x,a,fixed);q=physical(x,alt,fixed)
        elapsed=time.perf_counter()-before
        optimum,_,_=backward(x,m,b)
        gap=q[m]-optimum;old=b[m]-optimum;target=Fraction(row["target"])
        assert 0<=gap<=old
        rr.update(status="excluded" if gap<target else "demonstrated",old_gap=old/4,new_gap=gap/4,
                  target=float(target/4),incremental_wall_s=elapsed,threshold_crossing=gap<target<=old)
        rows.append(rr);raw.append(dict(case=x["id"],objective=m,witness=alt))
    with (out/"cases.csv").open("w") as f:
        w=csv.DictWriter(f,fieldnames=list(dict.fromkeys(k for r in rows for k in r)));w.writeheader();w.writerows(rows)
    (out/"witnesses.json.gz").write_bytes(gzip.compress(json.dumps(raw,separators=(",",":")).encode(),mtime=0))
    summary={}
    for m in ("service","cost"):
        rr=[r for r in rows if r["objective"]==m and r["status"]!="invalid"]
        summary[m]=dict(n=len(rr),improved=sum(r["new_gap"]<r["old_gap"] for r in rr),now_zero=sum(r["new_gap"]==0 for r in rr),
                        now_excluded=sum(r["status"]=="excluded" for r in rr),newly_excluded=sum(r["threshold_crossing"] for r in rr),
                        mean_old=sum(r["old_gap"] for r in rr)/len(rr),mean_new=sum(r["new_gap"] for r in rr)/len(rr),
                        median_extra_ms=1000*median(r["incremental_wall_s"] for r in rr),
                        residual_target_hits_by_regime=dict(Counter(r["regime"] for r in rr if r["status"]=="demonstrated")))
    summary["elapsed_s"]=time.perf_counter()-start
    summary["design_sha256"]=sha256((HERE/"design.md").read_bytes()).hexdigest()
    (out/"summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    print(json.dumps(summary))


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--data",required=True,type=Path);p.add_argument("--out",required=True,type=Path)
    args=p.parse_args();compare(args.data,args.out)
