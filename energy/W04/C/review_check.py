"""Independent post-freeze check of reduced starts and saved AC final states.

The frozen start generator supplies only the DC point. Network physics, input
parsing, voltage/current reconstruction, and the bounds checks below are local.
"""
import argparse
import json
import re
import sys
from decimal import Decimal
from pathlib import Path

import numpy as np
from scipy import sparse as sp
from scipy.sparse.csgraph import shortest_path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "foundation/src"))
from ac import starts, read_case, CFG


def table(text, name):
    body = re.search(r"mpc\."+name+r"\s*=\s*\[(.*?)\];", text, re.S)[1]
    return np.stack([np.fromstring(line, sep=" ") for line in body.split(";") if line.strip()])


def get_network(path):
    text = re.sub(r"%[^\n]*", "", path.read_text())
    bus, gen, br, cost = [table(text, k) for k in ("bus","gen","branch","gencost")]
    active = gen[:,7] > 0
    gen, cost, br = gen[active], cost[active,4:7], br[br[:,10]>0]
    base = float(re.search(r"mpc\.baseMVA\s*=\s*([^;]+)",text)[1])
    idx = {int(r[0]):j for j,r in enumerate(bus)}
    ij = np.arange(len(br))
    fr,to = (np.array([idx[int(i)] for i in br[:,j]]) for j in [0,1])
    gb = np.array([idx[int(x)] for x in gen[:,0]])
    def connect(vertices):
        return sp.csr_matrix((np.ones(len(br)),(ij, vertices)),shape=(len(br),len(bus)))
    cf,ct=map(connect,(fr,to))
    tap=np.where(br[:,8]==0,1,br[:,8])*np.exp(1j*np.deg2rad(br[:,9]))
    y=1/(br[:,2]+1j*br[:,3]); bcharge=.5j*br[:,4]
    Yf=sp.diags((y+bcharge)/abs(tap)**2)@cf - sp.diags(y/np.conjugate(tap))@ct
    Yt=sp.diags(y+bcharge)@ct - sp.diags(y/tap)@cf
    ref=int(np.flatnonzero(bus[:,1]==3)[0])
    def powers(v,theta):
        vphasor=v*np.exp(1j*theta)
        sf=base*(cf@vphasor)*np.conjugate(Yf@vphasor)
        st=base*(ct@vphasor)*np.conjugate(Yt@vphasor)
        load=bus[:,2]+1j*bus[:,3]+(bus[:,4]-1j*bus[:,5])*v*v
        return cf.T@sf + ct.T@st + load,sf,st
    def check(v,theta,p,q):
        demand,sf,st=powers(v,theta)
        gen_bus=np.bincount(gb,weights=p,minlength=len(bus))+1j*np.bincount(gb,weights=q,minlength=len(bus))
        nodal_residual=gen_bus-demand
        box=max(0.,float(max(np.max(p-gen[:,8]),np.max(gen[:,9]-p),np.max(q-gen[:,3]),np.max(gen[:,4]-q))))
        cap=br[:,5]>0
        thermal=max(0.,float(max(np.max(abs(sf[cap])-br[cap,5]),np.max(abs(st[cap])-br[cap,5]))))
        bus_voltage=max(0.,float(max(np.max(v-bus[:,11]),np.max(bus[:,12]-v))))
        da=np.rad2deg(theta[fr]-theta[to])
        branch_angle=max(0.,float(max(np.max(da-br[:,12]),np.max(br[:,11]-da))))
        balance=float(max(np.max(abs(nodal_residual.real)),np.max(abs(nodal_residual.imag))))
        fin=all(np.isfinite(x).all() for x in (v,theta,p,q))
        theta_box=max(0.,float(np.max(abs(theta))-2*np.pi))
        valid=fin and max(box,thermal,balance)<=CFG['physics_tol_MVA'] and bus_voltage<=1e-7 and branch_angle<=CFG['angle_tol_deg'] and theta_box<=1e-7 and abs(theta[ref])<1e-7
        return dict(box=box,thermal=thermal,balance=balance,bus_voltage=bus_voltage,branch_angle=branch_angle,
                    extra_theta_box=theta_box,finite=bool(fin),valid=bool(valid),
                    cost=float(np.sum(cost[:,0]*p*p+cost[:,1]*p+cost[:,2])))
    return bus,gen,br,gb,fr,to,base,powers,check


def run(raw):
    case_rows=[];witnesses=0;disagreements=[];maxcost=0;maxphysical=0;maxangle=0.0;counts=0
    baseline = {}
    for line in (HERE.parent / "foundation/inputs/ac/BASELINE.md").read_text().splitlines():
        if line.startswith("| pglib_opf_case"):
            cells = [x.strip() for x in line.strip("|").split("|")]
            try: baseline[cells[0]] = Decimal(cells[4])
            except ArithmeticError: pass
    for path in sorted((HERE/"inputs").glob("*.m")):
        bus,gen,br,gb,fr,to,base,powers,check=get_network(path)
        v,th,p0,q0=starts(read_case(path),True)
        p0=p0*base;q0=q0*base
        gbuses=np.unique(gb)
        degree=np.bincount(np.r_[fr,to],minlength=len(bus))
        pivots={i:max(np.flatnonzero(gb==i),key=lambda g:gen[g,8]-gen[g,9]+gen[g,3]-gen[g,4]) for i in gbuses}
        demand,_,_=powers(v,th)
        def lift(keep):
            p,q=p0.copy(),q0.copy()
            for i,j in pivots.items():
                if not keep(i):continue
                elsewhere=np.flatnonzero((gb==i)&(np.arange(len(gen))!=j))
                r=demand[i]-sum(p[elsewhere]+1j*q[elsewhere])
                p[j],q[j]=r.real,r.imag
            return p,q
        all_p,all_q=lift(lambda i:True)
        low_p,low_q=lift(lambda i:degree[i]<=3)
        maxdiff=max(float(np.max(abs(all_p-low_p))),float(np.max(abs(all_q-low_q))))
        floor_applicable=bool(np.all(bus[:,4]>=0) and np.all(br[:,2]>=0))
        network=sp.csr_matrix((np.ones(len(fr)),(fr,to)),shape=(len(bus),len(bus)))
        hops=shortest_path(network,directed=False,indices=int(np.flatnonzero(bus[:,1]==3)[0]),unweighted=True)
        if not np.all((br[:,11]==-30)&(br[:,12]==30)):
            raise ValueError("The 30 degree graph-bound diagnostic requires these branch limits")
        case_rows.append(dict(case=path.stem,generator_buses=len(pivots),low_degree_pivots=int(sum(degree[i]<=3 for i in pivots)),
                       original_dc_box=check(v,th,p0,q0)['box'],all_pivot_lifted_box=check(v,th,all_p,all_q)['box'],
                       low_degree_lifted_box=check(v,th,low_p,low_q)['box'],max_all_vs_low_p_or_q_MW_MVAr=maxdiff,
                       nonnegative_network_terms=floor_applicable,reference_eccentricity=int(max(hops)),
                       buses_exceeding_simple_360_degree_path_bound=int(sum(hops>12))))
        printed = baseline[path.stem]
        halfwidth = .5 * 10.**printed.as_tuple().exponent
        public_errors = []
        outside = []
        for file in raw.glob(path.stem+"_*.json"):
            r=json.loads(file.read_text())
            if r["case"]!=path.stem:continue
            counts+=1
            if "variables" not in r:continue
            vals=[np.asarray(v) for v in r['variables']]
            c=check(*vals);witnesses+=1
            maxangle=max(maxangle,float(np.max(abs(vals[1]))))
            maxcost=max(maxcost,abs(c['cost']-r['check']['cost']))
            diffs=[abs(c[k]-r['check'][a]) for k,a in [('box','generator_box_MW_MVAr'),('thermal','thermal_MVA'),('balance','balance_MVA'),('branch_angle','angle_degrees'),('bus_voltage','voltage_pu')]]
            maxphysical=max(maxphysical,max(diffs))
            if c['valid'] and r['elapsed']<=12:
                gap=abs(c['cost']-float(printed))
                public_errors.append(gap)
                if gap>halfwidth:
                    outside.append(file.name)
            if c['valid']!=r['check']['valid'] or not c['finite'] or c['extra_theta_box']>1e-7:
                disagreements.append(file.name)
        case_rows[-1].update(public_ac_printed=str(printed),public_rounding_halfwidth=halfwidth,
                             validated_ontime_public_comparisons=len(public_errors),
                             outside_publisher_rounding_interval=outside,
                             max_absolute_published_difference=max(public_errors,default=None))
    return dict(cases=case_rows,scheduled_records=counts,witnesses=witnesses,disagreements=disagreements,maximum_saved_absolute_angle_radians=maxangle,
                maximum_cost_difference=maxcost,maximum_recomputed_constraint_metric_difference=maxphysical)


if __name__ == "__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--raw",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    a.out.write_text(json.dumps(run(a.raw),indent=2)+"\n")
