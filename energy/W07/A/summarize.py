"""Descriptive equal-design-weight summaries. Timing applies to the archived run only."""
from collections import Counter
from fractions import Fraction as F
from pathlib import Path
from statistics import median
import csv,json,sys
def summarize(folder):
    rows=list(csv.DictReader((folder/'families.csv').open())); records=json.loads((folder/'records.json').read_text())
    mean=lambda vals:sum(vals,F())/len(vals)
    def data(key):return [F(row[key]) for row in rows]
    def derived(f):
        x=[f({k:F(r[k]) for k in ['baseline','causal','PF','prefix1','prefix3','penalty','analytic','threshold']}) for r in rows]
        return {'mean':str(mean(x)),'min':str(min(x)),'max':str(max(x)),'zero':x.count(0)}
    report={'mean_opportunity_ceiling':{k:derived(lambda r,k=k:r['baseline']-r[k]) for k in
                   ['analytic','PF','prefix1','prefix3','penalty','causal']},
            'clairvoyance_advantage':derived(lambda r:r['causal']-r['PF']),
            'penalty_minus_PF_counts':dict(Counter('weaker' if a<b else 'stronger' if a>b else 'equal' for a,b in zip(data('penalty'),data('PF')))),
            'first_stop':dict(Counter(r['first_stop'] for r in rows)),
            'by_stratum':{k:dict(decisions=dict(Counter(r['decision'] for r in rows if r['stratum']==k)),
                                 gains=[r['gain'] for r in rows if r['stratum']==k]) for k in sorted({r['stratum'] for r in rows})},
            'timing':{},'direct_cheaper_than_stage':sum(float(r['direct_s'])<float(r['staged_s']) for r in rows)}
    for arm in ('staged','direct','milp','shadow'):
        aa=[r for r in records if r['arm']==arm]
        report['timing'][arm]={
            'cold_total_s':sum(r['process_seconds'] for r in aa),'median_cold_s':median(r['process_seconds'] for r in aa),
            'sum_baseline_build_and_check_s':sum(r['times']['baseline_build']+r['times']['baseline_check'] for r in aa),
            'sum_tier_build_solve_s':sum(s['solve'] for r in aa for s in r['stages']),
            'sum_tier_check_s':sum(s['check'] for r in aa for s in r['stages']),
            'worker_total_s':sum(r['worker_seconds'] for r in aa),'peak_rss_native':max(r['rss_native'] for r in aa)}
    return report
if __name__=='__main__':
    print(json.dumps(summarize(Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).parent/'results'),indent=2))
