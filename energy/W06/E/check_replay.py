"""Compare a fresh replay with the release, ignoring only host-specific clocks and run identifiers."""
import argparse
import gzip
import hashlib
import json
import zipfile
from fractions import Fraction as F
from pathlib import Path

HERE=Path(__file__).resolve().parent

def read(p):return json.loads(gzip.decompress(p.read_bytes()) if p.suffix==".gz" else p.read_bytes())


def compare(ref,other,review,out):
    states=actions=hours=panels=0
    for f in (ref/"inputs").glob("*.gz"):
        assert f.read_bytes()==(other/"inputs"/f.name).read_bytes();panels+=1
    for c in sorted((ref/"results").glob("cert_*.json.gz")):
        a=read(c);b=read(other/"results"/c.name)
        for name in a:
            aa=a[name];bb=b[name];aa.pop("elapsed_ns");bb.pop("elapsed_ns")
            assert aa==bb;states+=sum(map(len,aa["potentials"]))
        tag=c.name[len("cert_"):]
        for k in ("baseline_","online_","supplement_"):
            a=read(ref/"results"/(k+tag));b=read(other/"results"/(k+tag))
            for name in a:
                x=a[name];y=b[name]
                if name=="reset":assert x==y;continue
                x.pop("wall_ns");y.pop("wall_ns")
                p=x.pop("actions");q=y.pop("actions")
                assert x==y and len(p)==len(q)
                assert all(i[:4]+i[5:]==j[:4]+j[5:] for i,j in zip(p,q))
                actions+=len(p)
        hours+=len(p)
    for f in ("splice.json.gz","analytic_stock.json.gz","results.json","splice_audit.json"):
        a=read(ref/"historical"/f);b=read(other/"historical"/f)
        if isinstance(a,list):
            for i,j in zip(a,b):i.pop("seconds");j.pop("seconds")
        else:
            a.pop("wall_seconds",None);b.pop("wall_seconds",None)
        assert a==b,f
    with zipfile.ZipFile(review) as archive:
        reviewers={r["case"]:r for r in json.loads(archive.read("opportunity_review_results.json"))["cases"]}
    an=read(ref/"historical/analytic_stock.json.gz")["originals"];deltas={}
    for mode,field in [("same_stock","equal_stock_ceiling_USD"),("min_stock","floor_ceiling_USD")]:
        deltas[mode]=max(float(abs(F(*r[field])-F(*reviewers[r["ids"][0]][mode]["gap_exact"]))) for r in an)
    assert max(deltas.values())<1e-12
    record={"path_inputs_identical_including_two_development":panels,"holdout_site_hours":hours,
            "identical_Bellman_state_potentials_including_terminal":states,"identical_applied_hourly_actions_and_fallbacks_excluding_clocks":actions,
            "historical_diagnostics_identical_excluding_clocks":True,"max_USD_discrepancy_independent_analytic_vs_supplied_W05_LP_upper_ceilings":deltas,
            "fresh_replay_wall_seconds_by_step":read(other/"run_clock.json")}
    out.write_text(json.dumps(record,indent=2)+"\n")
    print(json.dumps(record))
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("fresh",type=Path);p.add_argument("review",type=Path);p.add_argument("out",type=Path)
    a=p.parse_args();compare(HERE,a.fresh,a.review,a.out)
