"""W03-only forensic replay, separate from W04 holdout controllers and comparisons."""
import json
from pathlib import Path
import numpy as np
import campaign as edition


def main():
    old=edition.old;root=edition.ROOT
    historical=edition.read(edition.FOUNDATION/'inputs/load_forecasts.json')['cases']
    case=next(c for c in historical if c['id']=='outage_reserve_864')
    archiv=next(r for r in edition.read(edition.FOUNDATION/'results/E/runs.json') if r['case']==case['id'] and r['method']=='rolling_mpc')
    review=edition.read(root/'inputs/reviewer_864.json')['trajectory']
    differences=np.max(abs(np.array(archiv['actions'])-review['actions']),axis=1)
    first=int(np.flatnonzero(differences>1e-6)[0])
    positions={k:[] for k in ('mac','linux_injected','det_ds','det_ipm')}
    actual=np.asarray(case['load']);orig_lp=edition.linprog
    for kind,rows in positions.items():
        energy=edition.P['initial'];prev=edition.P['previous']
        for h,issue in enumerate(case['issues']):
            idx=np.asarray(issue['valid']);args=(np.asarray(issue['load']),np.asarray(issue['available']),
                np.asarray(case['floor'])[idx],np.asarray(case['reserve'])[idx],energy,prev)
            if kind.startswith('det'):
                def wrapper(*a,**kw):
                    if kind=='det_ipm':kw['method']='highs-ipm'
                    return orig_lp(*a,**kw)
                edition.linprog=wrapper
                plan,_=edition.lex_plan(*args)
            else:
                plan,_=old.lp(*args)
            act=plan[0]
            if kind=='linux_injected' and h==first:act=np.asarray(review['actions'][h])
            assert old.check(act,energy,prev,actual[h],case['available'][h],case['floor'][h],case['reserve'][h])<1e-6
            energy=act[4];prev=act[0];rows.append(act.tolist())
        edition.linprog=orig_lp
    def delta(left,right):return float(abs(np.asarray(left)-np.asarray(right)).max())
    rec=dict(first_divergent_zero_based_hour=first,mac_replay_max_action_error=delta(positions['mac'],archiv['actions']),
             replay_with_one_linux_action_max_error_vs_linux=delta(positions['linux_injected'],review['actions']),
             deterministic_ds_vs_ipm_max_action_difference=delta(positions['det_ds'],positions['det_ipm']),
             unserved_by_rerun={k:sum(a[3] for a in rs) for k,rs in positions.items()},actions=positions)
    edition.dump(root/'results/linux_case_diagnostic.json',rec)


if __name__=='__main__':main()
