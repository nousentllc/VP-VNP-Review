"""Freeze the data files and compute offline headroom before development of any new controller."""
import argparse
import hashlib
import json
import platform
import sys
import time
from datetime import datetime,timezone
from pathlib import Path

import numpy as np

from plant import HERE, DEV, SEEDS, generate, read, save
from dispatch import offline,simulate,stock_diagnostics


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def run(out):
    start=time.perf_counter_ns()
    protocol=HERE/"protocol"
    for line in (protocol/"freeze.sha256").read_text().splitlines():
        h,name=line.split("  ",1)
        assert digest(HERE/name)==h, name
    dev=[]
    for seed in DEV:
        p=generate(seed,7)
        save(out/"inputs"/f"development_{seed}.json.gz",p)
        dev.append(p)
    fit={x:sum(simulate(p,"price",x)["cents"] for p in dev) for x in (55,70,85)}
    ref=min(fit,key=fit.get)
    save(out/"results"/"price_rule_fit.json",{"development_total_cents":fit,"selected":ref})
    summary=[]
    for seed in SEEDS:
        for days in (7,30):
            clock=time.perf_counter_ns()
            p=generate(seed,days);tag=f"{seed}_{days}"
            save(out/"inputs"/f"{tag}.json.gz",p)
            gen_ns=time.perf_counter_ns()-clock
            baseline=simulate(p,"price",ref)
            fill=simulate(p,"fill",ref,terminal_match=False)
            cert=stock_diagnostics(p["actual"],fill["final_soc"])
            reset=[]
            for k in range(days):
                rows=p["actual"][24*k:24*k+24]
                fragment={"actual":rows,"issued_H12":[[r] for r in rows]}
                daily=simulate(fragment,"fill",ref,terminal_match=False)
                same=offline(rows,daily["final_soc"],50,"flat",certificate=False)
                loose=offline(rows,None,50,"flat",certificate=False)
                reset.append(dict(end=daily["final_soc"],same=same["cents"],loose=loose["cents"]))
            ceiling=baseline["cents"]-cert["market_match9"]["cents"]
            assert ceiling>=0
            save(out/"results"/f"cert_{tag}.json.gz",cert)
            save(out/"results"/f"baseline_{tag}.json.gz",dict(price=baseline,free_fill=fill,reset=reset))
            rec=dict(seed=seed,days=days,generate_save_ns=gen_ns,case_wall_ns=time.perf_counter_ns()-clock,
                     ceiling_cents=ceiling,price_cents=baseline["cents"],free_fill_end=fill["final_soc"],
                     offline_cents={n:v["cents"] for n,v in cert.items()},
                     reset_stock_gap_cents=sum(r["same"]-r["loose"] for r in reset))
            summary.append(rec)
    eligible={d:sum(r["ceiling_cents"] for r in summary if r["days"]==d)>len(SEEDS)*d*1500 for d in (7,30)}
    save(out/"results"/"gate.json",dict(created_utc=datetime.now(timezone.utc).isoformat(),seeds=SEEDS,
         practical_threshold_USD_per_day=15,ref=ref,eligible=eligible,cases=summary,
         wall_ns=time.perf_counter_ns()-start,python=sys.version,numpy=np.__version__,platform=platform.platform()))
    print("Gate",eligible,"price reference",ref)


if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--out",type=Path,default=HERE)
    run(parser.parse_args().out)
