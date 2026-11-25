"""Fresh primary evaluations, followed by full same-signal deterministic replay."""
import argparse
from policies import *

def check_lock():
    lock=read(ROOT/'protocol/freeze.json')
    for homes,k in [(ROOT,'sha256'),(W04,'w04_sha256')]:
        for name,value in lock[k].items():
            if digest(homes/name)!=value:raise ValueError(f'changed input {name}')
    return lock

def run(out,control=None):
    check_lock();out=Path(out)
    if out.exists():raise FileExistsError(out)
    out.parent.mkdir(parents=True,exist_ok=True)
    signals={}
    if control is not None:
        with gzip.open(control,'rt') as records:
            for line in records:
                r=json.loads(line)
                if 'error' not in r:signals[r['case'],r['arm']]=[d['clock_fallback'] for d in r['decisions']]
    data=read(ROOT/'inputs/holdout.json.gz')['cases']
    config=read(ROOT/'protocol/development.json')['cfg']
    with gzip.open(out,'wt',compresslevel=3) as f:
        for i,c in enumerate(data):
            arms=ARMS[i%len(ARMS):]+ARMS[:i%len(ARMS)]
            for arm in arms:
                try:r=policy(c,arm,config,clock_signals=signals[c['id'],arm] if control else None)
                except Exception as err:
                    r=dict(case=c['id'],arm=arm,seed=c['seed'],regime=c['regime'],panel=c['panel'],error=repr(err))
                f.write(json.dumps(r,default=clean,separators=(',',':'),allow_nan=False)+'\n')
            if (i+1)%12==0:
                f.flush();print(f'{i+1}/{len(data)} scenario days',flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',required=True,type=Path);p.add_argument('--signals-from',type=Path)
    arg=p.parse_args();run(arg.out,arg.signals_from)
