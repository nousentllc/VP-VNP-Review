"""Prespecified matched comparisons aggregated once per seed; independent units are latent families."""
import csv
from fractions import Fraction as F
from pathlib import Path
import statistics
import sys
import json
import numpy as np
from model import read,save,SEEDS,BUDGETS,CALENDARS, direction
from small import wear_prices,revalue
from historical.rainflow import stack_histogram

def main(out):
    currents=[];raw=[];facts=[];costs=[wear_prices(r) for r in (50,150,300)]
    for seed in SEEDS:
        panel=read(out/'inputs'/f'{seed}.json.gz');rows=panel['actual'];n=len(rows)
        for K in BUDGETS:
            standby=read(out/'outcomes'/f'{seed}_{K}_standby.json.gz')
            for calendar,req in CALENDARS.items():
                path=read(out/'outcomes'/f'{seed}_{K}_{calendar}.json.gz')
                for name,record in path.items():
                    done=record['failed'] is None
                    steps=record['steps'];ending=record['closing_soc']
                    actual=[r[2] for r in steps];nom=[r[0] for r in steps];calls=[r[1] for r in steps]
                    ac=lambda q:11*max(q,0)+9*min(q,0)
                    n0=0 if not steps else len(steps)
                    state=[9]+[r[3] for r in steps]
                    def cash_without_wear(r):return r[5]+r[7]+r[8]
                    revals=[record['net_cents']-record['subtotal_cents'][1]+revalue(state,p) if done else None for p in costs]
                    def gain(t):
                        base=standby[name]['steps'][t]
                        return sum(steps[t][5:9])-sum(base[5:9])
                    first=next((i for i,c in enumerate(calls) if c),len(steps))
                    during=sum(gain(i) for i in range(len(steps)) if calls[i]) if done else None
                    recovery=sum(gain(i) for i in range(first,len(steps)) if not calls[i]) if done else None
                    if done:assert during+recovery==record['net_cents']-standby[name]['net_cents']
                    initial_budget=K
                    unavailable=0;exhausted=0
                    for t,c in enumerate(calls):
                        if t in req:
                            if not initial_budget:exhausted+=1
                            elif not rows[t][4]:unavailable+=1
                        initial_budget-=int(c!=0)
                    unavailable_hours=sum(direction(t)!=0 and not rows[t][4] for t in range(n0))
                    pending=lambda t,delay,col:sum(panel['arrivals'][u][col] for u in range(max(0,t-delay+1),t+1))
                    raw.append(dict(seed=seed,K=K,calendar=calendar,arm=name,completed=done,first_failure=record['failed'],
                        evaluable_hours=n0,activated_hours=sum(map(bool,calls)),delivered_up=sum(c<0 for c in calls),
                        delivered_down=sum(c>0 for c in calls),up_response_deciMWh=sum(ac(q)-ac(a) for q,a,c in zip(nom,actual,calls) if c<0),
                        down_response_deciMWh=sum(ac(a)-ac(q) for q,a,c in zip(nom,actual,calls) if c>0),
                        unavailable_standby_hours=unavailable_hours,forgone_standby_cents=800*unavailable_hours,
                        unavailable_requests_with_positive_budget=unavailable,calendar_attempts_after_budget_spent=exhausted,
                        energy_cents=record['subtotal_cents'][0],wear_cents=record['subtotal_cents'][1],capacity_receipts_cents=-record['subtotal_cents'][2],
                        activation_receipts_cents=-record['subtotal_cents'][3],service_interruption_deciMWh_on_completed_hours=0,
                        protected_deciMWh=sum(r[1] for r in rows[:n0]),high_jobs_served=sum(r[2] for r in rows[:n0]),
                        low_jobs_served=sum(r[3] for r in rows[:n0]),midnight_pending_jobs=[(pending(t,2,0),pending(t,5,1)) for t in (23,47) if t<n0],
                        gross_import_deciMWh=sum(r[1]+7*r[2]+4*r[3]+ac(a) for r,a in zip(rows,actual)),
                        closure_SOC=ending,terminal_inventory_credit_cents=-45000 if done else None,
                        cost_cents=record['net_cents'],activation_hour_cost_change_cents=during,
                        subsequent_noncall_cost_change_cents=recovery,rain_50_cents=revals[0],rain_150_cents=revals[1],rain_300_cents=revals[2],
                        feedback_fallbacks=sum(r[9] for r in steps)))
                for rate,costkey in [(0,'cost_cents'),(50,'rain_50_cents'),(150,'rain_150_cents'),(300,'rain_300_cents')]:
                    arms={r['arm']:r for r in raw[-4:]}
                    facts.append(dict(seed=seed,K=K,calendar=calendar,rate=rate,
                        gain=(arms['robust_three'][costkey]-arms['robust_single'][costkey])/300))
    save(out/'activated_components.json.gz',raw)
    gates=read(out/'gates.json')['cases'];groups=[]
    for K in BUDGETS:
        r=[x for x in raw if x['K']==K];g=[x for x in gates if x['K']==K]
        means={}
        for rate in (0,50,150,300):
            x=[statistics.mean(z['gain'] for z in facts if z['seed']==s and z['K']==K and z['rate']==rate) for s in SEEDS]
            rng=np.random.default_rng(175079);reps=np.mean(rng.choice(np.array(x),(20000,len(x)),replace=True),axis=1)
            means[rate]=dict(per_seed=x,mean_USD_day=statistics.mean(x),CI95_conditional_percentile=list(np.percentile(reps,[2.5,97.5])),
                             attained_inclusive_15=sum(a>=15 for a in x))
        baseline=[z for z in r if z['arm']=='robust_three'];ceil=[z['ceiling_cents']/300 for z in g]
        ag={f:sum(z[f] for z in baseline) for f in ('delivered_up','delivered_down','up_response_deciMWh','down_response_deciMWh',
                  'unavailable_standby_hours','unavailable_requests_with_positive_budget','calendar_attempts_after_budget_spent',
                  'energy_cents','wear_cents','activation_receipts_cents','capacity_receipts_cents','forgone_standby_cents','gross_import_deciMWh',
                  'service_interruption_deciMWh_on_completed_hours','activation_hour_cost_change_cents','subsequent_noncall_cost_change_cents')}
        groups.append(dict(K=K,calendar_seed_paths=len(g),exclusions=sum(x['excludes_15_per_day'] for x in g),mean_ceiling_USD_day=statistics.mean(ceil),
                      weighted_panel_ceiling_excludes_15=statistics.mean(ceil)<15,ceiling_range=[min(ceil),max(ceil)],
                      W06_and_robust_failures={arm:sum(not z['completed'] for z in r if z['arm']==arm) for arm in {z['arm'] for z in r}},
                      realized=ag,gain_single_over_three=means))
    save(out/'summary.json',dict(groups=groups))
if __name__=='__main__':main(Path(sys.argv[1]))
