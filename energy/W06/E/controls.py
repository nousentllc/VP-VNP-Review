"""Adversarial tests of evidence rejection and exact-arithmetic scope."""
import argparse
import copy
from fractions import Fraction as F
from pathlib import Path
from audit import check_offline,forecast_check,trajectory
from plant import HERE,read,save


def rejects(fn):
    try:fn()
    except (AssertionError,ValueError):return True
    return False


def run(out):
    p=read(out/"inputs/69103_7.json.gz");x=read(out/"results/online_69103_7.json.gz")["continuation"]
    cap=read(out/"results/cert_69103_7.json.gz")["market_match9"]
    q=copy.deepcopy(x);q["actions"][0][1]+=1
    u=copy.deepcopy(p);u["issued_H12"][0][2][0]+=1
    v=copy.deepcopy(cap);v["potentials"][0][37]+=1
    tests={"mutated_inventory_rejected":rejects(lambda:trajectory(p["actual"],q)),
           "nonissued_peek_rejected":rejects(lambda:forecast_check(u)),
           "false_one_cent_Bellman_bound_rejected":rejects(lambda:check_offline(p["actual"],v,{}))}
    assert all(tests.values())
    # One-hour cost minimization min q subject to q>=1/2. Integer grid lower 1 exceeds continuous 1/2.
    assert min(q for q in (0,1) if q>=F(1,2))>F(1,2)
    tests["integral_plant_lower_bound_can_exceed_continuous_optimum"]=True
    # Same hourly service and final stock can save money under varying prices at unit efficiency.
    # Unit net load in both hours. Idle imports [1,1]; arbitrage imports [2,0].
    assert 1*10+1*100-(2*10+0*100)==90
    tests["equal_stock_equal_service_variable_price_counterexample_saving_USD"]=90
    save(out/"results/controls.json",tests)
if __name__=="__main__":
    op=argparse.ArgumentParser();op.add_argument("--out",type=Path,default=HERE);run(op.parse_args().out)
