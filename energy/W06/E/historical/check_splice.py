"""Check the stored splice LP multipliers directly with plant equations, without SciPy or an optimizer."""
import argparse
import gzip
import json
from fractions import Fraction as F
from pathlib import Path
from zipfile import ZipFile
from replay import reconstruct


def run(w05,artifact,out):
    with ZipFile(w05) as z:
        frozen=json.loads(gzip.decompress(z.read("Energy_Explorations/W05/E/inputs/holdout.json.gz")))
    p=frozen["parameters"];inputs={r["id"]:r for r in frozen["cases"]}
    cases=json.loads(gzip.decompress(artifact.read_bytes()));checked=0
    for result in cases:
        e=F(p["initial"]);g=F(p["previous"]);plant=[]
        for name in result["ids"]:
            c=inputs[name];timeline=reconstruct(c,dict(p,initial=e,previous=g))
            for t,(_,_,_,shed,_) in enumerate(timeline):
                av=F(p["power"])*bool(c["available"][t])
                plant.append((F(c["load"][t])-shed,av,max(0,av-F(c["reserve"][t])),F(c["floor"][t])))
            g=timeline[-1][0];e=timeline[-1][4]
        last=len(plant)-1
        for arm,certificate in result["arms"].items():
            y=[F(*v) for v in certificate["eq_duals"]];z=[F(*v) for v in certificate["le_duals"]]
            assert len(y)==len(z)==2*len(plant) and all(a<=0 for a in z)
            lb=F(0)
            for t,(served,cp,dp,lo) in enumerate(plant):
                power,storage=y[2*t:2*t+2];plus,minus=z[2*t:2*t+2]
                nxt=y[2*t+3] if t<last else 0
                forward=z[2*t+2]-z[2*t+3] if t<last else 0
                c_grid=50-power-plus+minus+forward
                c_charge=10+power+F(p["eta_c"])*storage
                c_discharge=10-power-F(1/p["eta_d"])*storage
                c_stock=(-50 if t==last else 0)-storage+nxt
                hi=F(p["energy"])
                if arm=="same_stock" and t==last:lo=hi=e
                lb+=min(0,c_grid*F(p["grid_cap"]))+min(0,c_charge*cp)+min(0,c_discharge*dp)+min(lo*c_stock,hi*c_stock)
                lb+=power*served+(plus+minus)*F(p["ramp"])
                if t==0:lb+=storage*F(p["initial"])+(plus-minus)*F(p["previous"])
            assert lb==F(*certificate["lower"])
            assert F(*result["fill_cost"])-lb==F(*certificate["gap"])
            checked+=1
    out.write_text(json.dumps({"splices":len(cases),"boxed_rational_LP_bounds_checked":checked,"solver_calls":0},indent=2)+"\n")
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("w05",type=Path);p.add_argument("artifact",type=Path);p.add_argument("out",type=Path);a=p.parse_args();run(a.w05,a.artifact,a.out)
