"""Check the flat-price energy identity and a ramp-envelope discharge lower bound in exact arithmetic."""
import argparse
from fractions import Fraction as F
import gzip
import json
import time
from pathlib import Path
from zipfile import ZipFile

from replay import reconstruct


def cert(cases,p):
    soc=F(p["initial"]);grid=F(p["previous"]);served=[];caps=[];cc=dd=F(0)
    eta=F(p["eta_c"]);draw=F(1/p["eta_d"])
    for c in cases:
        rows=reconstruct(c,dict(p,initial=soc,previous=grid))
        for t,(g,ch,dis,shed,e) in enumerate(rows):
            served.append(F(c["load"][t])-shed)
            caps.append(F(p["power"])*bool(c["available"][t]))
            cc+=ch;dd+=dis
        soc=rows[-1][4];grid=rows[-1][0]
    p0=w0=v=F(50);w0=F(10)
    ks=(p0+w0)/eta-v;kd=(p0+w0)*draw/eta+w0-p0
    actual=p0*(sum(served)+cc-dd)+w0*(cc+dd)-v*soc
    assert actual==p0*sum(served)-v*F(p["initial"])+ks*(soc-F(p["initial"]))+kd*dd
    loose_cap=[min(F(p["grid_cap"]),y+av) for y,av in zip(served,caps)]
    cap=loose_cap[:];r=F(p["ramp"]);gp=F(p["previous"])
    for t in range(len(cap)):
        cap[t]=min(cap[t],gp+r);gp=cap[t]
    for t in range(len(cap)-2,-1,-1):cap[t]=min(cap[t],cap[t+1]+r)
    excess=dd-sum(max(0,y-g) for y,g in zip(served,cap));assert excess>=0
    fixed=kd*excess;floor=F(cases[-1]["floor"][-1]);inv=ks*(soc-floor)
    pair=lambda x:[x.numerator,x.denominator]
    return dict(ids=[x["id"] for x in cases],days=len(cases),stock_MWh=pair(soc),excess_discharge_MWh=pair(excess),
                equal_stock_ceiling_USD=pair(fixed),terminal_term_USD=pair(inv),floor_ceiling_USD=pair(inv+fixed),
                equal_stock_zero=fixed==0,loose_rounded_USD_per_day=float((fixed+inv)/len(cases)))


def main(w05,spliced,out):
    tic=time.perf_counter()
    with ZipFile(w05) as z:
        p=json.loads(gzip.decompress(z.read("Energy_Explorations/W05/E/inputs/holdout.json.gz")))
    rows={r["id"]:r for r in p["cases"]}
    ones=[cert([r],p["parameters"]) for r in rows.values()]
    long=json.loads(gzip.decompress(spliced.read_bytes()))
    combined=[cert([rows[n] for n in x["ids"]],p["parameters"]) for x in long]
    # Both are upper bounds; no universal ordering is assumed.
    diffs=[abs(float(F(*v["floor_ceiling_USD"])-F(*s["arms"]["min_stock"]["gap"]))) for v,s in zip(combined,long)]
    record=dict(originals=ones,splices=combined,n_single_exact_zero=sum(r["equal_stock_zero"] for r in ones),
                n_splice_exact_zero=sum(r["equal_stock_zero"] for r in combined),max_abs_splice_ceiling_difference_USD=max(diffs),
                wall_seconds=time.perf_counter()-tic)
    out.write_bytes(gzip.compress(json.dumps(record,separators=(",",":")).encode(),mtime=0))
    print(record["n_single_exact_zero"],record["n_splice_exact_zero"],max(diffs))
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("w05",type=Path);p.add_argument("splices",type=Path);p.add_argument("out",type=Path);a=p.parse_args();main(a.w05,a.splices,a.out)
