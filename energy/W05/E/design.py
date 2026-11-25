"""W04-only calibration and frozen W05 sample construction."""
import argparse,datetime
from policies import *
PRIMARY=list(range(15101,15161))
EXTERNAL=list(range(22501,22525))

def alternative(seeds):
    """Different load/forecast DGP with longer rectangular workloads and AR innovations."""
    cases=[]
    for seed in seeds:
        rng=np.random.default_rng(seed);noise=np.random.default_rng(seed+910000)
        start=int(rng.integers(4,11));duration=int(rng.integers(7,11))
        h=np.arange(24);base=84.+3*np.cos((h-5)*2*np.pi/24)+rng.uniform(-2,2)
        dayplan=base+(h>=start)*(h<start+duration)*rng.uniform(22,41)
        second=int(rng.integers(14,21))
        dayplan+=((h>=second)&(h<second+2))*rng.uniform(4,19)
        err=np.zeros(24);jumps=rng.normal(0,3,24);jumps[int(rng.integers(4,18))]+=rng.uniform(6,15)
        for t in range(24):err[t]=(.78*err[t-1] if t else 0.)+jumps[t]
        actual=np.maximum(80.,dayplan+err)
        outage=int(rng.integers(5,13));outlen=int(rng.integers(2,5))
        eps=noise.normal(0,2.3,(24,12));eps=np.cumsum(eps,axis=1)*.62
        for reg in ('base','biased_forecast','outage_reserve'):
            floor=(48 if reg=='outage_reserve' else 35)+(95-(48 if reg=='outage_reserve' else 35))*np.clip((h-17)/6,0.,1.)
            available=np.ones(24,dtype=bool);rs=np.zeros(24)
            if reg=='outage_reserve':
                available[outage:outage+outlen]=False;rs[6:17]=10.
            issues=[]
            for t in range(24):
                idx=np.arange(t,min(24,t+12));lead=idx-t
                bias=np.minimum(lead,7)*(-1.45 if reg=='biased_forecast' else 0.)
                fc=np.maximum(80.,dayplan[idx]+.55**lead*err[t]+eps[t,:len(idx)]+bias)
                fc[0]=actual[t]
                issues.append(dict(issue=t,valid=idx,load=fc,available=np.where(lead<=1,available[idx],True)))
            cases.append(dict(id=f'alt_{reg}_{seed}',panel='alternative',regime=reg,seed=seed,load=actual,
                             available=available,floor=floor,reserve=rs,issues=issues))
    return cases

def development():
    cases=read(W04/'E/inputs/holdout.json.gz')['cases']; old_extra=read(W04/'E/protocol/development.json')['calibration']['extra']
    cfg=dict(old_extra=old_extra,learned=fit(cases),rules={},switch_tail_difference=-4.)
    scores={};records=[];physical={}
    def loss(r):return sum(v[3] for v in r['actions'])
    for h in HORIZONS:
        group={}
        for option in RULES:
            rows=[policy(c,f'rule{h}',cfg,override_rule=option,clock_signals=[False]*24) for c in cases]
            group[option]=float(np.mean([loss(r) for r in rows]))
        cfg['rules'][str(h)]=min(group,key=group.get)
        scores[f'rule{h}']=group
    methods=['rule12','nestedrule6','none12','w0412','nested6','adaptive']
    # Prefix parsing for model names w04H is defined explicitly in policies.
    candidates={}
    for arm in methods:
        losses=[]
        for c in cases:
            r=policy(c,arm,cfg,clock_signals=[False]*24)
            losses.append(loss(r));records.append(dict(id=c['id'],arm=arm,unserved=loss(r)))
        candidates[arm]=float(np.mean(losses))
    cfg['strongest12']=min(candidates,key=candidates.get)
    controls=[]
    for c in cases[::8]:
        for hour in (0,10,20):
            issue=c['issues'][hour];idx=np.array(issue['valid'])[:6]
            args=(np.array(issue['load'])[:6],np.array(issue['available'])[:6],np.array(c['floor'])[idx],np.array(c['reserve'])[idx],95.,85.,110.)
            x,s=lex(*args);y,v=old.lex_plan(*args)
            diff=float(np.max(abs(x[0]-y[0])))
            if diff>TOL:raise ValueError((c['id'],hour,diff))
            controls.append(dict(case=c['id'],hour=hour,first_action_discrepancy=diff,stages=s))
    return dict(cfg=cfg,rule_development=scores,comparator12_development=candidates,comparators_by_case=records,
                interface_regression=controls,training_ids=[c['id'] for c in cases])

def freeze():
    dev=read(ROOT/'protocol/development.json')
    cases=old.panel(PRIMARY)['cases']
    for c in cases:c['panel']='primary'
    cases+=alternative(EXTERNAL)
    dump(ROOT/'inputs/holdout.json.gz',dict(parameters=P,cases=cases))
    lockfiles=['policies.py','design.py','run.py','audit.py','protocol/design.md','protocol/development.json','inputs/holdout.json.gz']
    oldfiles=['E/campaign.py','E/protocol/development.json','E/inputs/holdout.json.gz','foundation/src/common.py',
              'foundation/src/load_control.py','foundation/requirements.txt','foundation/protocol/design.json']
    lock=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),sha256={x:digest(ROOT/x) for x in lockfiles},
              w04_sha256={x:digest(W04/x) for x in oldfiles},primary=PRIMARY,alternative=EXTERNAL,
              rules=dev['cfg']['rules'],strongest12=dev['cfg']['strongest12'],arms=ARMS,hardware=os.uname().machine,
              python=sys.version,highs=highspy.Highs().version(),numpy=np.__version__,scipy=old.scipy.__version__,threads=1)
    dump(ROOT/'protocol/freeze.json',lock)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['develop','freeze']);arg=ap.parse_args()
    if arg.action=='develop':dump(ROOT/'protocol/development.json',development())
    else:freeze()
