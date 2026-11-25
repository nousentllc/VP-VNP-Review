"""Independently attribute reported UC starts and check consistency of numerical bounds."""
import argparse
import csv
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

ARMS = ("group_start", "lp_start", "permanent", "full")
OUTER_STAGES = {"full", "recovered_full", "outer_lp"}
PREPARATION = {"paired", "sign_repair"}
START_LINE = re.compile(r"MIP start solution is feasible, objective value is ([-+0-9.eE]+)",re.I)
SNAPSHOTS = (5, 15, 30, 45)


def cell(folder, dataset, issues):
    arm = next(a for a in ARMS if folder.name.endswith("_"+a))
    case,horizon = folder.name[:-len(arm)-1].rsplit("_",1)
    supervisor = json.loads((folder/"supervisor.json").read_text())
    source = folder/"record.json"
    record = json.loads(source.read_text()) if source.exists() else {"events":[],"stages":[]}
    tag = [dataset,case,int(horizon),arm]
    events = [e for e in record["events"] if e["t"] <= 45]
    us = [e for e in events if "U" in e]
    ls = [e for e in events if "L" in e]
    for es,field,sgn in [(us,"U",-1),(ls,"L",1)]:
        vals = [e[field] for e in es]
        if not all(math.isfinite(v) for v in vals) or any(sgn*(b-a)<=0 for a,b in zip(vals,vals[1:])):
            issues.append([*tag,"nonfinite or nonmonotone",field])
    if any(e["stage"] not in OUTER_STAGES for e in ls):
        issues.append([*tag,"restricted model lower bound entered full scoring"])
    for deadline in SNAPSHOTS:
        by_u = [e["U"] for e in us if e["t"] <= deadline]
        by_l = [e["L"] for e in ls if e["t"] <= deadline]
        if by_u and by_l and max(by_l)>min(by_u)+1e-4:
            issues.append([*tag,"within-arm inversion",deadline])
    rec = next((s for s in record["stages"] if s["stage"]=="recovered_full"),{})
    prep = [e for e in us if e["stage"] in PREPARATION]
    recovered = [e for e in us if e["stage"]=="recovered_full"]
    text = (folder/"recovered_full.log").read_text(errors="replace") if (folder/"recovered_full.log").exists() else ""
    confirmed = [float(v) for v in START_LINE.findall(text)]
    offered = rec.get("transfer_cost")
    candidate = prep[-1]["U"] if prep else None
    if offered is not None and (candidate is None or abs(candidate-offered)>1e-5):
        issues.append([*tag,"submitted objective differs from pre-recovery incumbent",offered,candidate])
    if confirmed:
        ref = offered if offered is not None else candidate
        if ref is None or any(abs(v-ref)>max(1e-5,1e-10*abs(ref)) for v in confirmed):
            issues.append([*tag,"solver log start objective does not match recorded candidate",confirmed,ref])
        transfer = "confirmed_in_solver_log"
    elif offered is not None:
        transfer = "set_solution_recorded_no_feasibility_ack"
    elif not rec or "t_start" not in rec:
        transfer = "no_recovery_stage_started"
    elif candidate is not None and "status" not in rec:
        transfer = "unknown_interrupted_after_preparation"
    elif candidate is not None:
        transfer = "candidate_available_no_submission_record"
    else:
        transfer = "no_preparation_candidate"
    if not us:
        source_label = "no_validated_schedule"
    elif us[-1]["stage"] == "full":
        source_label = "direct_full_search"
    elif us[-1]["stage"] in PREPARATION:
        if arm=="permanent": source_label = "permanent_restriction_only"
        elif rec and "t_start" in rec: source_label = "retained_preparation_incumbent"
        else: source_label = "preparation_only_no_recovery_started"
    elif recovered:
        if confirmed: source_label = "improved_after_confirmed_start"
        elif offered is not None: source_label = "improved_after_unconfirmed_submission"
        elif candidate is not None: source_label = "recovered_with_unknown_transfer"
        else: source_label = "unrestricted_discovery_without_start"
    else:
        raise ValueError(("unknown incumbent stage",tag,us[-1]["stage"]))
    row=dict(panel=dataset,case=case,hours=int(horizon),arm=arm,
             guard_killed=supervisor["killed"],worker_checkpoint=source.exists(),recovery_started="t_start" in rec,
             prep_U=candidate,set_solution_status=rec.get("transfer_status"),offered_U=offered,
             transfer=transfer,log_start_U=confirmed[-1] if confirmed else None,
             recovered_improvements=len(recovered),incumbent_events=len(us),numerical_bound_events=len(ls),
             final_U=us[-1]["U"] if us else None,final_L=ls[-1]["L"] if ls else None,
             final_U_source=source_label,latest_U_stage=us[-1]["stage"] if us else None)
    return row,ls


def audit(primary,serial):
    rows,issues=[],[]
    all_bounds=defaultdict(list)
    for which,root in [("primary",primary),("serial",serial)]:
        jobs=sorted(p.parent for p in root.glob("*/supervisor.json"))
        if len(jobs)!=24:
            raise ValueError(f"{which}: expected 24 completed supervisors, found {len(jobs)}")
        for folder in jobs:
            row,lower=cell(folder,which,issues)
            rows.append(row)
            key=(row["case"],row["hours"])
            all_bounds[key].extend((e["L"],which,row["arm"],e["stage"]) for e in lower)
    keys=[(r["panel"],r["case"],r["hours"],r["arm"]) for r in rows]
    if len(set(keys))!=48 or {k[1:] for k in keys if k[0]=="primary"}!={k[1:] for k in keys if k[0]=="serial"}:
        raise ValueError("Panel cells do not match")
    cross=[]
    for (name,t),bounds in sorted(all_bounds.items()):
        uppers=[r["final_U"] for r in rows if (r["case"],r["hours"])==(name,t) and r["final_U"] is not None]
        best=min(uppers) if uppers else None
        max_l=max((e[0] for e in bounds),default=None)
        count=0
        if best is not None:
            count=len(bounds)
            for value,panel,arm,stage in bounds:
                if value>best+1e-4:issues.append([panel,name,t,arm,"cross-arm inversion",stage,value,best])
        cross.append(dict(case=name,hours=t,available_upper=best,highest_reported_lower=max_l,
                          lower_events=len(bounds),compared_against_known_upper=count))
    by_panel={}
    for key in ("primary","serial"):
        group=[r for r in rows if r["panel"]==key]
        by_panel[key]={"guard_kills":sum(r["guard_killed"] for r in group),
                       "no_first_checkpoint":sum(not r["worker_checkpoint"] for r in group),
                       "arms":{}}
        for arm in ARMS:
            selected=[r for r in group if r["arm"]==arm]
            by_panel[key]["arms"][arm]={"cells":len(selected),
                 "validated":sum(r["final_U"] is not None for r in selected),
                 "set_solution_recorded":sum(r["offered_U"] is not None for r in selected),
                 "log_confirmed":sum(r["log_start_U"] is not None for r in selected),
                 "final_incumbent_source":dict(Counter(r["final_U_source"] for r in selected)),
                 "transfer_evidence":dict(Counter(r["transfer"] for r in selected))}
    return rows,dict(panels=by_panel,cross_arm_consistency=cross,issues=issues,
        scope="Numerical consistency only. LP objective discounts and MIP duals lack independent exact dual validation.")


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--primary",type=Path,required=True)
    parser.add_argument("--serial",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    rows,summary=audit(args.primary,args.serial)
    args.out.mkdir(parents=True,exist_ok=False)
    with (args.out/"cell_attribution.csv").open("w",newline="") as output:
        writer=csv.DictWriter(output,fieldnames=list(rows[0]))
        writer.writeheader();writer.writerows(rows)
    (args.out/"transfer_review.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
    if summary["issues"]:raise SystemExit("Trace audit issues are recorded in transfer_review.json")
