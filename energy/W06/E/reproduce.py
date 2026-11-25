"""Run a clean end-to-end W06-E reproduction or recheck the supplied fresh evidence."""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE=Path(__file__).resolve().parent


def main(args):
    out=args.out.resolve()
    if out==HERE or HERE in out.parents or out.exists() and any(out.iterdir()):
        raise ValueError("Choose an empty output directory outside the released E tree.")
    out.mkdir(parents=True,exist_ok=True)
    timings={}
    def cmd(script,*items):
        t=time.perf_counter()
        subprocess.run([sys.executable,str(HERE/script),*map(str,items)],check=True,
                       env={**os.environ,"PYTHONDONTWRITEBYTECODE":"1","OPENBLAS_NUM_THREADS":"1"})
        timings[str(script)]=time.perf_counter()-t
    if args.mode=="audit":
        shutil.copytree(HERE/"inputs",out/"inputs");shutil.copytree(HERE/"results",out/"results")
        cmd("audit.py","--out",out);cmd("controls.py","--out",out)
        from audit import trajectory,load
        sup=load(out/"results/supplement_summary.json")
        for r in sup["cases"]:
            tag=f'{r["seed"]}_{r["days"]}'
            p=load(out/"inputs"/f"{tag}.json.gz");controls=load(out/"results"/f"supplement_{tag}.json.gz")
            for n,x in controls.items():assert trajectory(p["actual"],x)==r["details"][n]
    else:
        (out/"historical").mkdir()
        locks={args.w05:"3cb69e43c49820a767884bee6dd1d5ff0adb279af2398a4e820f3bd9abdf3fce",
               args.review:"bda0a8aebc7ffae15468cdc3a76850067cef36e2690ca8dd8a2cb90516d9448b"}
        for path,h in locks.items():
            if hashlib.sha256(path.read_bytes()).hexdigest()!=h:raise ValueError(path)
        cmd("historical/replay.py",args.w05,args.review,out/"historical/results.json")
        cmd("gate.py","--out",out);cmd("compare.py","--out",out);cmd("audit.py","--out",out)
        cmd("supplement.py","--out",out);cmd("controls.py","--out",out)
        cmd("historical/splice.py",args.w05,out/"historical/splice.json.gz")
        cmd("historical/analytic_stock.py",args.w05,out/"historical/splice.json.gz",out/"historical/analytic_stock.json.gz")
        cmd("historical/check_splice.py",args.w05,out/"historical/splice.json.gz",out/"historical/splice_audit.json")
    (out/"run_clock.json").write_text(json.dumps(timings,indent=2)+"\n")


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("mode",choices=["audit","run"]);p.add_argument("--out",required=True,type=Path)
    dep=HERE.parent/"dependencies";p.add_argument("--w05",type=Path,default=dep/"W05_Energy_Experiments.zip")
    p.add_argument("--review",type=Path,default=dep/"CRGC_W05_Independent_Opportunity_Review.zip")
    main(p.parse_args())
