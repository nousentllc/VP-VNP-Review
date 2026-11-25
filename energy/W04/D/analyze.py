"""Case-level UC service, warm starts, and matched feasible cost comparisons."""
import csv
import json
import sys
from pathlib import Path

def run(archive, analysis):
    with (analysis / "snapshots.csv").open() as stream:
        rows = list(csv.DictReader(stream))
    if len(rows)!=24 or len({(r['case'],r['hours'],r['arm']) for r in rows})!=24:
        raise ValueError("UC panel denominator")
    summaries=[]
    for arm in ("full","lp_start","group_start","permanent"):
        part=[r for r in rows if r["arm"]==arm]
        counters={}
        for r in part:
            folder=archive/f'{r["case"]}_{r["hours"]}_{arm}'
            if not (folder/'record.json').exists(): label="before_worker_ready"
            elif not r['build_s']:label="during_build_or_before_checkpoint"
            elif not r['U45']:label="no_validated_schedule"
            else:label="validated_schedule"
            counters[label]=counters.get(label,0)+1
        summaries.append(dict(arm=arm,unit_cases=len(part),valid_at={str(d):sum(bool(r["U"+str(d)]) for r in part) for d in [5,15,30,45]},
                target=sum(r["target"]=="True" for r in part),solver_confirmed_start=sum(r["solver_confirmed_start"]=="True" for r in part),
                guards=sum(r["external_guard"]=="True" for r in part),outcomes=counters))
    pairs=[]
    for r in rows:
        if r["arm"]!="group_start":continue
        for comp in ("full","lp_start","permanent"):
            b=next(a for a in rows if a["case"]==r["case"] and a["hours"]==r["hours"] and a["arm"]==comp)
            u,bv=r["U45"],b["U45"]
            diff=(float(u)-float(bv))/max(1,abs(float(bv))) if u and bv else None
            pairs.append(dict(case=r["case"],hours=r["hours"],compared_to=comp,group_U=u,baseline_U=bv,
                fractional_cost_difference=diff,practical_win=None if diff is None else diff < -.001))
    with (analysis/"paired_45s.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(pairs[0]));w.writeheader();w.writerows(pairs)
    (analysis/"summary.json").write_text(json.dumps(summaries,indent=2)+"\n")

if __name__=="__main__":
    run(Path(sys.argv[1]),Path(sys.argv[2]))
