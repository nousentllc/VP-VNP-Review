"""Observational second pass. Keep returned plans verbatim while running the frozen controller."""
import argparse
import gzip
import json
from pathlib import Path

import campaign as campaign


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--plans',type=Path,required=True)
    args=parser.parse_args()
    for path in (args.out,args.plans):
        if path.exists():raise FileExistsError(path)
        path.parent.mkdir(parents=True,exist_ok=True)
    for name,sha in campaign.read(campaign.ROOT/'protocol/freeze.json')['sha256'].items():
        assert campaign.digest(campaign.ROOT/name)==sha
    cases=campaign.read(campaign.ROOT/'inputs/holdout.json.gz')['cases']
    fit=campaign.read(campaign.ROOT/'protocol/development.json')['calibration']
    plans=[]
    def capture(fn):
        def wrapped(*a,**kw):
            result=fn(*a,**kw)
            plans.append(result[0])
            return result
        return wrapped
    campaign.lex_plan=capture(campaign.lex_plan)
    campaign.old.lp=capture(campaign.old.lp)
    with gzip.open(args.out,'wt') as output,gzip.open(args.plans,'wt') as trace:
        for i,case in enumerate(cases):
            arms=campaign.POLICIES[i%len(campaign.POLICIES):]+campaign.POLICIES[:i%len(campaign.POLICIES)]
            for policy in arms:
                plans.clear()
                rec=campaign.simulate(case,policy,fit)
                output.write(json.dumps(rec,allow_nan=False)+'\n')
                targets=[]
                if policy.startswith('rule'):
                    for h,issue in enumerate(case['issues']):
                        H=rec['decisions'][h]['horizon']
                        floor=max(case['floor'][k] for k in issue['valid'][:H])
                        deficit=sum(max(0,x-campaign.P['grid_cap']) for x in issue['load'][1:H])
                        targets.append(min(campaign.P['energy'],max(campaign.P['initial'],floor+deficit/campaign.P['eta_d'])))
                trace.write(json.dumps(dict(case=case['id'],policy=policy,rule_target_if_recharging=targets,
                                            predicted_plans=[None if p is None else p.tolist() for p in plans]),
                                       separators=(',',':'),allow_nan=False)+'\n')
            print(case['id'],flush=True)


if __name__=='__main__':main()
