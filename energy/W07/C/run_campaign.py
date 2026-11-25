"""Run a separate measured subprocess for each case, preserving errors and receipts."""
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
ROOT = Path(__file__).resolve().parent
def run_job(out, key, command):
    folder = out / "logs"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / (key + ".json")
    if path.exists():
        raise FileExistsError(path)
    start = time.perf_counter()
    with (folder / (key + ".log")).open("w") as stream:
        res = subprocess.run(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT,
                             env=dict(os.environ, OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1",
                                      PYTHONDONTWRITEBYTECODE="1", PYTHONHASHSEED="902"))
    path.write_text(json.dumps(dict(job=key, command=[str(v) for v in command[1:]], returncode=res.returncode,
                                    process_wall_s=time.perf_counter()-start), indent=2)+"\n")
    print(key, res.returncode, flush=True)
def main():
    ap=argparse.ArgumentParser();ap.add_argument("operation",choices=["solve","check"]);ap.add_argument("track",choices=["ac","uc"]);ap.add_argument("out",type=Path);ap.add_argument("--case");args=ap.parse_args()
    out=args.out.resolve();check=args.operation=="check"; track=args.track;fn="audit" if check else "run"
    for p in sorted((ROOT/"inputs").glob("*.m" if track=="ac" else "20*.json")):
        if args.case and args.case!=p.stem:continue
        for horizon in ([None] if track=="ac" else [24,48]):
            name=p.stem if horizon is None else f"{p.stem}_{horizon}"
            d=out/(track+"_results")/name
            if not check and (d/"summary.json").exists():raise FileExistsError(d)
            module="ac" if track=="ac" else "commitment"
            code=f"from {module} import {fn};from pathlib import Path;{fn}(Path({str(p)!r}),"+("" if horizon is None else f"{horizon},")+f"Path({str(d)!r}))"
            run_job(out,fn+"_"+name,[sys.executable,"-c",code])
            if not (d/"summary.json").exists():continue
            info=json.loads((d/"summary.json").read_text())
            if info['U'] is None or info['excluded']:continue
            mod="clique" if track=="ac" else "uc_tree";sub="results" if track=="ac" else "uc_results"
            dest=out/"exploratory"/sub/name
            code=f"from {mod} import {fn};from pathlib import Path;{fn}(Path({str(p)!r}),"+("" if horizon is None else f"{horizon},")+f"Path({str(d)!r}),Path({str(dest)!r}))"
            run_job(out,fn+"_"+mod+"_"+name,[sys.executable,"-c",code])
if __name__=="__main__":main()
