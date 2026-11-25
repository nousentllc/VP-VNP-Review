"""Recalculate the W04-E archived and conditional-clock diagnostics into fresh output."""
import argparse
import gzip
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def panel_keys(path):
    seen=set()
    with gzip.open(path,'rt') as stream:
        for line in stream:
            row=json.loads(line)
            key=(row['case'],row['policy'])
            if key in seen:
                raise ValueError(f'Duplicate trajectory in {path.name}: {key}')
            seen.add(key)
    return seen


def run(primary,repeat,plans,output):
    primary,repeat,plans,output=(p.resolve() for p in (primary,repeat,plans,output))
    if output==ROOT.parent or ROOT.parent in output.parents:
        raise ValueError('Choose a fresh output path outside the evidence archive.')
    if primary==repeat:
        raise ValueError('Supply two separately executed trajectory files.')
    keys=panel_keys(primary)
    if len(keys)!=864 or panel_keys(repeat)!=keys or panel_keys(plans)!=keys:
        raise ValueError('Expected the same 864 unique frozen day-policy pairs in all three inputs.')
    for name,expected in json.loads((ROOT/'protocol/freeze.json').read_text())['sha256'].items():
        if digest(ROOT/name)!=expected:
            raise ValueError(f'Frozen input mismatch for {name}')
    output.mkdir(parents=True,exist_ok=False)

    # The W03 utility initializes its results path at import. Give it this disposable destination.
    os.environ['W03_RESULTS']=str(output)
    sys.dont_write_bytecode=True
    import campaign  # Sets the campaign’s numerical thread limits before NumPy is imported.
    import analyze
    import check_plans
    import deadline_sensitivity
    import pareto
    import replay_deadlines
    import tail_accuracy

    analyze.run(primary,output/'primary_summary',repeat)
    analyze.run(repeat,output/'repeat_summary',None)
    check_plans.main(repeat,plans,output/'plan_validation.json')
    replay_deadlines.run(primary,repeat,output/'deadline_attribution.json')
    deadline_sensitivity.main(primary,repeat,output/'deadline_sensitivity.json')
    pareto.run(output/'primary_summary/scenario_metrics.csv',output/'pareto.csv')
    tail_accuracy.main(output/'tail_accuracy.csv')
    metadata={'trajectory_pairs':len(keys),
              'input_sha256':{label:digest(path) for label,path in [('primary',primary),('repeat',repeat),('plans',plans)]},
              'freeze_sha256':digest(ROOT/'protocol/freeze.json'),
              'clock_scope':'Primary and repeat gates use their original observed timings. '
                            'Supplementary reconstruction and conditional replay runtimes are new wall measurements.'}
    (output/'audit_inputs.json').write_text(json.dumps(metadata,indent=2)+'\n')


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    for name in ('primary','repeat','plans','out'):
        cli.add_argument('--'+name,type=Path,required=True)
    args=cli.parse_args()
    run(args.primary,args.repeat,args.plans,args.out)
