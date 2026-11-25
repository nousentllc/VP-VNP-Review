"""W05-A development, prospective input freeze and immutable holdout driver."""
import argparse
import datetime
import gzip
import json
import os
import platform
import sys
from pathlib import Path
from engine import ARMS, SEEDS, SIZES, FAMILIES, CLOCKS, HERE, W04, FOUND, digest, records, run_trial, hs

CONFIGS=[dict(effort=.05,reserve=.15,repair_share=.15),dict(effort=.15,reserve=.30,repair_share=.30)]
def write_gz(path,obj):
    with gzip.open(path,'wt') as f:json.dump(obj,f,allow_nan=False,separators=(',',':'))
def score(rows,arm):
    # Development rank: certified hits, number of available actions, paired fallback-scaled quality, then wall time.
    us=[min((v['U'] for v in r['events'] if 'U' in v),default=None) for r in rows]
    native=sum(any(s.get('numerical_native_lower') is not None and u is not None and s['return_time']<=2
                    and u-s['numerical_native_lower']<=.00002+.001*max(1,abs(u)) for s in r['stages']) for u,r in zip(us,rows))
    return [sum(r['target'] is not None for r in rows) if arm!='native_unmetered_certificate' else native,
            sum(u is not None for u in us),-sum(u/max(1,abs(r['fallback_cost'])) for u,r in zip(us,rows) if u is not None),
            -sum(r['wall'] for r in rows)]
def source_paths():
    return [HERE/'engine.py',HERE/'campaign.py',HERE/'audit.py',HERE/'protocol/plan.md',W04/'A/protocol/instances.json',
            FOUND/'src/battery_inputs.py',FOUND/'src/battery_model.py',FOUND/'src/battery_audit.py',FOUND/'src/common.py',
            FOUND/'protocol/design.json',FOUND/'requirements.txt']
def prepare(out):
    out.mkdir(exist_ok=True,parents=True)
    if (out/'freeze.json').exists():raise ValueError('Already frozen.')
    original=json.loads((W04/'A/protocol/instances.json').read_text())
    old=[v for v in original if v['id'] in ['ordinary_4x8_10403','forced_opposition_12x16_10403']]
    assert len(old)==2
    dev=[]
    for j,v in enumerate(old):
        a={**v,'fallback_supplied':True}
        for k,config in enumerate(CONFIGS):
            order=ARMS[j+k:]+ARMS[:j+k]
            for arm in order:
                dev.append(dict(config=k,trial=run_trial(a,arm,0,config)))
    write_gz(out/'development.json.gz',dev)
    settings={};scores={}
    for arm in ARMS:
        ranked=[score([q['trial'] for q in dev if q['config']==k and q['trial']['arm']==arm],arm) for k in range(2)]
        settings[arm]=CONFIGS[max(range(2),key=lambda k:ranked[k])];scores[arm]=ranked
    panel=records();assert not {v['seed'] for v in original}&set(SEEDS)
    assert len({v['generator_seed'] for v in panel}&{v['seed'] for v in original})==0
    write_gz(out/'instances.json.gz',panel)
    files={os.path.relpath(p,HERE):digest(p) for p in source_paths()}
    lock=dict(time_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),platform=platform.platform(),
              cpus=os.cpu_count(),python=sys.version,highs=hs.Highs().version(),threads=1,governing_protocol='W05/protocol/W05_Research_Protocol.md',
              fresh_cluster_seeds=SEEDS,sizes=SIZES,families=FAMILIES,replicates=3,arms=ARMS,snapshots_s=CLOCKS,
              dev_configurations=CONFIGS,dev_scores=scores,selected=settings,sha256=files,
              assets_sha256={p:digest(out/p) for p in ['instances.json.gz','development.json.gz']})
    (out/'freeze.json').write_text(json.dumps(lock,indent=2)+'\n')
def run(out):
    p=HERE/'protocol';lock=json.loads((p/'freeze.json').read_text())
    for file,required in lock['sha256'].items():
        if digest(HERE/file)!=required:raise ValueError('Source mismatch: '+file)
    for file,required in lock['assets_sha256'].items():
        if digest(p/file)!=required:raise ValueError('Asset mismatch: '+file)
    with gzip.open(p/'instances.json.gz','rt') as f:panel=json.load(f)
    out.mkdir(exist_ok=True,parents=True)
    dest=out/'trials.jsonl.gz'
    if dest.exists():raise ValueError('Use a fresh destination.')
    with gzip.open(dest,'wt') as f:
        for j,a in enumerate(panel):
            for rep in range(3):
                k=(j+rep*2)%len(ARMS)
                for arm in ARMS[k:]+ARMS[:k]:
                    raw=run_trial(a,arm,rep,lock['selected'][arm])
                    f.write(json.dumps(raw,allow_nan=False,separators=(',',':'))+'\n')
            f.flush();print(a['id'],flush=True)
if __name__=='__main__':
    cli=argparse.ArgumentParser();cli.add_argument('action',choices=['prepare','run']);cli.add_argument('--out',type=Path,required=True)
    args=cli.parse_args();(prepare if args.action=='prepare' else run)(args.out)
