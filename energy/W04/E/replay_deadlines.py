"""Conditional reproduction: inject the recorded deadline signal into cases with unequal actions."""
import gzip
import json
import time
from pathlib import Path
import numpy as np

import campaign

ROOT = Path(__file__).resolve().parent


def load(path):
    with gzip.open(path,'rt') as f:
        return {(row['case'],row['policy']):row for row in map(json.loads,f)}


class RecordedDeadlines:
    """Substitute original recorded elapsed durations solely at the frozen gate's clock reads."""
    def __init__(self, row):
        values=[]
        if row['policy']=='offline':
            values.extend([0.,row['offline_solve_seconds']])
        for issue in row['decisions']:
            values.extend([0.,issue['ready_seconds']])
        self.values=iter(values)

    def perf_counter(self):
        return next(self.values)


def run(primary=ROOT/'results/holdout.jsonl.gz',repeat=ROOT/'results/repeat.jsonl.gz',
        output_path=ROOT/'results/deadline_attribution.json'):
    for name,sha in campaign.read(ROOT/'protocol/freeze.json')['sha256'].items():
        assert campaign.digest(ROOT/name)==sha
    a=load(primary)
    b=load(repeat)
    cases={c['id']:c for c in campaign.read(ROOT/'inputs/holdout.json.gz')['cases']}
    fit=campaign.read(ROOT/'protocol/development.json')['calibration']
    metadata=[]
    equal=0;gates_differ=0;changes=0
    for key,row in a.items():
        second=b[key]
        changed=float(abs(np.array(row['actions'])-np.array(second['actions'])).max())
        gates1=[x['fallback'] for x in row['decisions']]
        gates2=[x['fallback'] for x in second['decisions']]
        if gates1!=gates2:
            gates_differ+=1
        if changed==0:
            equal+=1
            continue
        # Rerun the same stateful solver and decision branch at the original timeout pattern.
        start=time.perf_counter()
        try:
            campaign.time=RecordedDeadlines(row)
            result=campaign.simulate(cases[key[0]],key[1],fit)
            assert next(campaign.time.values,None) is None
        finally:
            campaign.time=time
        error=float(abs(np.array(row['actions'])-np.array(result['actions'])).max())
        if error>0:changes+=1
        metadata.append(dict(case=key[0],policy=key[1],max_action_difference_uncontrolled=changed,
                             first_fallback=gates1,second_fallback=gates2,original_clock_max_action_difference=error,
                             seconds_for_rerun=time.perf_counter()-start))
    output=dict(scope='Secondary diagnostic. Primary timing and service outcomes retain all actual measured deadlines.',
                live_replay_trajectories_equal=equal,live_trajectories_with_different_fallbacks=gates_differ,
                rerun_count=len(metadata),original_clock_trajectories_with_unequal_actions=changes,
                records=metadata)
    output_path.write_text(json.dumps(output,indent=2)+'\n')

if __name__=='__main__':
    run()
