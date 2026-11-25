"""Rerun the released one-call study and challenge the second call independently."""
from pathlib import Path
import json
import gzip
import subprocess
import sys
import time

BASE = Path(__file__).resolve().parent
HIST = BASE / 'historical'
FOLLOW = HIST / 'reserve_activation_followup'


def main(target):
    start = time.perf_counter()
    target.mkdir(parents=True,exist_ok=True)
    for name in ('run','check'):
        with (target/f'{name}.log').open('w') as log:
            subprocess.run([sys.executable,str(FOLLOW/f'{name}.py'),'--out',str(target)],stdout=log,check=True)
    actual = json.loads((target/'audit.json').read_text())
    orig = json.loads((HIST/'archived_audit.json').read_text())
    assert actual['panels']==orig['panels']
    skip={'wall_s','msmax','audit_seconds'}
    def stable(node):
        if isinstance(node,list): return [stable(v) for v in node]
        if isinstance(node,dict): return {k:stable(v) for k,v in node.items() if k not in skip}
        return node
    assert stable(actual['by_case'])==stable(orig['by_case'])
    def read(name): return json.loads(gzip.decompress(name.read_bytes()))
    online=read(target/'online_69103_7.json.gz')
    rows=read(HIST/'inputs/69103_7.json.gz')['actual']
    witness={}
    for name,plan in online.items():
        path=plan['actions']; s=path[3][1]; prev=path[3][0]; q=path[4][0]
        if (s,prev,q)!=(9,0,1): continue
        a=q+1; end=s+a
        assert rows[4][7]==rows[5][7]==1 and a==2 and end==11
        def phys(c):
            return (abs(c)<=rows[5][4] and abs(c-a)<=2 and 2<=end+c<=11 and
                    (c>=0 or end+c>=rows[5][5]) and 0<=sum((rows[5][1],7*rows[5][2],4*rows[5][3]))+c*(11 if c>0 else 9)<=90)
        nominal=[c for c in range(-2,3) if phys(c) and -rows[5][4]+rows[5][6]<=c<=rows[5][4]-rows[5][7]]
        passes=[c for c in nominal if phys(c+1)]
        assert nominal==[0] and not passes
        witness[name]={'first_hour':4,'state':[s,prev],'nominal':q,'first_down_applied':a,'after':[end,a],
                       'next_nominals':nominal,'next_down_end_SOC':end+1,'feasible_two_call_responses':passes}
    assert witness
    result={'replicated_panels':actual['panels'],'counterexample':witness,'seconds':time.perf_counter()-start,
            'raw_by_case_matches_historical_reference_excluding_timers':True}
    (target/'regression.json').write_text(json.dumps(result,indent=2)+'\n')

if __name__=='__main__':main(Path(sys.argv[1]).resolve())
