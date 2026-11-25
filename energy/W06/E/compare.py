"""Execute the registered controller comparison after the exact opportunity gate."""
import argparse
import hashlib
import time
from pathlib import Path

from dispatch import simulate
from plant import HERE, DEV, SEEDS, read, save


def run(out):
    clock=time.perf_counter_ns()
    gate_path=out/"results/gate.json"
    gate=read(gate_path)
    ref=gate["ref"]
    selected=None
    if any(gate["eligible"].values()):
        dev=[read(out/"inputs"/f"development_{seed}.json.gz") for seed in DEV]
        fit={k:sum(simulate(panel,"continuation",ref,k)["cents"] for panel in dev)
             for k in [45,65,85]}
        selected=min(fit,key=fit.get)
        save(out/"results/continuation_fit.json",dict(development_total_cents=fit,selected=selected,
             prerequisite_gate_sha256=hashlib.sha256(gate_path.read_bytes()).hexdigest()))
    for s in SEEDS:
        for d in (7,30):
            tag=f"{s}_{d}";p=read(out/"inputs"/f"{tag}.json.gz")
            arms={method:simulate(p,method,ref) for method in ("fill","h6","h12")}
            if gate["eligible"][str(d)]:
                arms["continuation"]=simulate(p,"continuation",ref,selected)
            save(out/"results"/f"online_{tag}.json.gz",arms)
    save(out/"results/compare_clock.json",dict(wall_ns=time.perf_counter_ns()-clock))
    print("Fitted terminal credit",selected,"USD/MWh on two development paths.")
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--out",type=Path,default=HERE);run(p.parse_args().out)
