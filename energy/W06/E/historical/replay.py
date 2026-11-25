"""Run the archived economic review and independently reconstruct the causal greedy fill schedule."""
import argparse
import gzip
import hashlib
import json
import subprocess
import sys
import tempfile
import zipfile
from fractions import Fraction as Q
from pathlib import Path


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def reconstruct(case, p):
    soc, grid = Q(p["initial"]), Q(p["previous"])
    path = []
    for i, load_value in enumerate(case["load"]):
        load = Q(load_value)
        cap = min(Q(p["grid_cap"]), grid + Q(p["ramp"]))
        power = Q(p["power"]) * bool(case["available"][i])
        floor = Q(case["floor"][i])
        draw = Q(1 / p["eta_d"])
        efficiency = Q(p["eta_c"])
        discharge = min(max(0, power - Q(case["reserve"][i])), max(0, load - cap), max(0, soc - floor) / draw)
        capacity = (Q(p["energy"]) - soc) / efficiency
        charge = 0 if discharge else min(power, capacity, max(0, (floor-soc)/efficiency, min(capacity, max(0, cap-load))))
        previous = grid
        grid = min(cap, load+charge-discharge)
        shed = load-grid+charge-discharge
        soc += charge*efficiency-discharge*draw
        assert abs(grid-previous)<=Q(p["ramp"]) and floor<=soc<=Q(p["energy"])
        assert 0<=shed<=load-Q(p["facility"]) and charge*discharge==0
        path.append([Q(x) for x in (grid,charge,discharge,shed,soc)])
    return path


def replay(w05, review, out):
    start = __import__("time").perf_counter()
    with zipfile.ZipFile(w05) as packet, zipfile.ZipFile(review) as independent:
        assert packet.testzip() is None and independent.testzip() is None
        def data(name):
            return json.loads(gzip.decompress(packet.read("Energy_Explorations/W05/E/"+name)))
        panel=data("inputs/holdout.json.gz")
        stored={r["case"]:r for r in data("results/analysis/opportunity_certificates.json.gz")}
        live={r["case"]:r["actions"] for r in map(json.loads,gzip.decompress(packet.read("Energy_Explorations/W05/E/results/primary.jsonl.gz")).splitlines()) if r["arm"]=="rule12"}
        maxerror=0.
        for case in panel["cases"]:
            name=case["id"]
            actions=reconstruct(case,panel["parameters"])
            assert actions==[[Q(*v) for v in row] for row in stored[name]["primal"]]
            maxerror=max(maxerror,max(abs(float(v)-float(y)) for a,b in zip(actions,live[name]) for v,y in zip(a,b)))
        assert len(live)==len(stored)==len(panel["cases"])==252 and maxerror<1e-8
        with tempfile.TemporaryDirectory() as tmp:
            script=Path(tmp)/"opportunity_review.py"
            script.write_bytes(independent.read(script.name))
            output=Path(tmp)/"economic.json"
            subprocess.run([sys.executable,str(script),str(w05),str(output)],check=True,stdout=subprocess.DEVNULL)
            result=json.loads(output.read_text())
            original=json.loads(independent.read("opportunity_review_results.json"))
            for a,b in zip(result["cases"],original["cases"],strict=True):
                assert a["case"]==b["case"] and a["service_gap"]==b["service_gap"]
                for arm in ("same_stock","min_stock"):
                    assert a[arm]["success"] and a[arm]["gap_exact"]==b[arm]["gap_exact"]
            record={"W05_sha256":digest(w05),"review_sha256":digest(review),"exact_fill_trajectories":len(stored),"actions_per_trajectory":24,"fields_per_action":5,"max_difference_from_archived_online_fill":maxerror,"exact_economic_LP_gap_pairs":504,"summary":result["summary"],"wall_seconds":__import__("time").perf_counter()-start}
    Path(out).write_text(json.dumps(record,indent=2)+"\n")
    print("Matched 252 full exact greedy trajectories and all 504 historical exact gap fractions.")
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("w05",type=Path);p.add_argument("review",type=Path);p.add_argument("out",type=Path)
    a=p.parse_args();replay(a.w05,a.review,a.out)
