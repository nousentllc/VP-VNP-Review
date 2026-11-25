"""Check the post hoc flat-tariff specialization with exact archived rationals."""
import argparse
import gzip
import hashlib
import json
import math
from fractions import Fraction as Q
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parent
HISTORY = ROOT.parents[1]/"E/historical"
W05_DIGEST = "3cb69e43c49820a767884bee6dd1d5ff0adb279af2398a4e820f3bd9abdf3fce"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_gz(path):
    return json.loads(gzip.decompress(path.read_bytes()))


def envelope_floor(local, served, grid, previous, ramp):
    # Least upper envelope from ALL pairwise path distances, independent of the
    # forward/back sweeps used by track E. Scale to integers without rounding.
    unit = math.lcm(*(y.denominator for y in [*local, *served, previous, ramp]))
    bound = [int(y*unit) for y in local]
    step = int(ramp*unit)
    start = int(previous*unit)
    result = Q(0)
    for t, y in enumerate(served):
        cap = min(start + step*(t+1), min(v + step*abs(j-t) for j,v in enumerate(bound)))
        assert grid[t]*unit <= cap
        result += max(0, y-Q(cap,unit))
    return result


def path_witness(cases, parameters):
    ec = Q(parameters["eta_c"])
    b = Q(1.0/parameters["eta_d"])
    stock, grid = Q(parameters["initial"]), Q(parameters["previous"])
    rows = []
    for case in cases:
        for load, available, reserve, floor in zip(case["load"], case["available"], case["reserve"], case["floor"], strict=True):
            load, reserve, floor = map(Q, (load, reserve, floor))
            charger = Q(parameters["power"])*int(bool(available))
            reachable = min(Q(parameters["grid_cap"]), grid+Q(parameters["ramp"]))
            discharge = min(max(Q(0), charger-reserve), max(Q(0), load-reachable),
                            max(Q(0),stock-floor)/b)
            charge = Q(0)
            if discharge == 0:
                desired = max(Q(0), reachable-load, (floor-stock)/ec)
                charge = min(charger, (Q(parameters["energy"])-stock)/ec, desired)
            next_grid = min(reachable, load+charge-discharge)
            lost = load+charge-discharge-next_grid
            next_stock = stock+ec*charge-b*discharge
            assert abs(next_grid-grid) <= Q(parameters["ramp"])
            assert 0 <= next_grid <= Q(parameters["grid_cap"])
            assert floor <= next_stock <= Q(parameters["energy"])
            assert 0 <= lost <= load-Q(parameters["facility"])
            assert 0 <= charge <= charger and 0 <= discharge <= max(0,charger-reserve)
            assert charge*discharge == 0
            rows.append((next_grid, charge, discharge, lost, next_stock))
            grid, stock = next_grid, next_stock
    return rows


def run(w05, history):
    provenance = json.loads((ROOT/"inputs/source_lock.json").read_text())
    assert provenance["parent_archive_sha256"] == W05_DIGEST
    def source(part):
        name = "Energy_Explorations/W05/E/"+part
        lock = provenance["members"][name]
        packed = (ROOT/"inputs"/lock["file"]).read_bytes()
        assert hashlib.sha256(packed).hexdigest() == lock["sha256"]
        if w05 is not None:
            with ZipFile(w05) as z:
                assert z.read(name) == packed
        return json.loads(gzip.decompress(packed))
    if w05 is not None:
        assert digest(w05) == W05_DIGEST
    panel = source("inputs/holdout.json.gz")
    witnesses = {x["case"]:x["primal"] for x in source("results/analysis/opportunity_certificates.json.gz")}
    inputs = {c["id"]:c for c in panel["cases"]}
    p=panel["parameters"]
    ec, b = Q(p["eta_c"]), Q(1./p["eta_d"])
    price, wear, v = map(Q,(50,10,50))
    ks, kd = (price+wear)/ec-v, (price+wear)*b/ec+wear-price
    assert 0 < ec <= 1 <= b and v*ec <= price+wear and min(ks,kd)>0
    e = load_gz(history/"analytic_stock.json.gz")
    splices = load_gz(history/"splice.json.gz")
    packed = {tuple(r["ids"]):r for r in e["originals"]+e["splices"]}
    ids = [[r["id"]] for r in panel["cases"]] + [v["ids"] for v in splices]
    assert len(ids) == len(packed) == 264
    summaries=[]
    for names in ids:
        cases=[inputs[n] for n in names]
        trace=path_witness(cases,p)
        if len(names)==1:
            assert trace==[tuple(Q(*val) for val in row) for row in witnesses[names[0]]]
        cells=[(Q(load),Q(p["power"])*int(bool(av))) for c in cases for load,av in zip(c["load"],c["available"],strict=True)]
        served=[ld-row[3] for (ld,_),row in zip(cells,trace,strict=True)]
        caps=[min(Q(p["grid_cap"]),y+power) for y,(_,power) in zip(served,cells,strict=True)]
        g,ch,ds,lost,stock=zip(*trace,strict=True)
        minimum=envelope_floor(caps,served,g,Q(p["previous"]),Q(p["ramp"]))
        assert minimum==sum(ds) and sum(g)==sum(served)+sum(ch)-sum(ds)
        base=price*sum(g)+wear*(sum(ch)+sum(ds))-v*stock[-1]
        transformed=price*sum(served)-v*Q(p["initial"])+ks*(stock[-1]-Q(p["initial"]))+kd*sum(ds)
        assert base==transformed
        floor=Q(cases[-1]["floor"][-1])
        archived=packed[tuple(names)]
        gap=ks*(stock[-1]-floor)+kd*(sum(ds)-minimum)
        assert gap==Q(*archived["floor_ceiling_USD"])
        assert Q(*archived["equal_stock_ceiling_USD"])==0
        summaries.append({"ids":names,"days":len(names),"charge_AC_MWh":str(sum(ch)),"discharge_AC_MWh":str(sum(ds)),
                          "unavoidable_discharge_AC_MWh":str(minimum),"final_stored_MWh":str(stock[-1]),
                          "floor_stored_MWh":str(floor),"baseline_cost_USD":str(base),"fixed_stock_ceiling_USD":"0",
                          "floor_ceiling_USD":str(gap)})
    return {"study":"W06 post hoc verification of flat W05 tariff; original daily cases and their splices",
            "inputs":{"W05_archive_sha256":W05_DIGEST,"E_splice_digest":digest(history/"splice.json.gz"),
                      "E_analytic_digest":digest(history/"analytic_stock.json.gz")},
            "coefficients":{"p_grid":str(price),"w_throughput":str(wear),"v_stock":str(v),"eta_c":str(ec),
                            "stored_draw_per_AC_out":str(b),"ks":str(ks),"kd":str(kd)},
            "single_witnesses_matched":len(witnesses),"splices_checked":len(splices),
            "raw_hourly_transitions_checked":sum(r["days"]*24 for r in summaries),
            "scope":"Checked feasibility, identity, and analytical lower discharge floor. The floor-only ceiling need not be attainable.",
            "records":summaries}


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--w05-zip",type=Path,help="Optional original for byte comparison against bundled W05 members")
    p.add_argument("--history",default=HISTORY,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    data=run(a.w05_zip,a.history)
    with a.out.open("xb") as f:
        f.write(gzip.compress(json.dumps(data,separators=(",",":")).encode(),mtime=0))
    print(data["single_witnesses_matched"],data["splices_checked"],data["raw_hourly_transitions_checked"])
