"""Post-primary verification of every realized comparator nomination from current issued data alone."""
from collections import defaultdict
import gzip
import json
from pathlib import Path
import sys
import time
import numpy as np
from independent import ST,IX,read,BIG


def audit(source):
    torig=time.perf_counter();spec=read(source/'design.json')
    masks=np.array(read(source/'kernels.json.gz')['actions'],dtype=bool)
    # Row-sparse edge representation independent of the released vectorized lookahead.
    edges={}
    for t in range(72):
        for p in (0,1,2):
            for b in range(5):
                i,qi=np.nonzero(masks[t,p,b]);q=qi-2
                j=np.array([IX[ST[x][0]+y,y] for x,y in zip(i,q)],dtype=int)
                dg=np.where(q>0,11*q,9*q); wear=abs(dg)*80+600*(abs(q)==2)
                edges[t,p,b]=i,qi,j,dg,wear
    checked=0;failed=0;midnights=0;worst=0;booked=0;misses=0;solves=0
    for s in spec['seeds']:
        case=read(source/'inputs'/f'{s}.json.gz');observed=defaultdict(list)
        for t,row in enumerate(case['actual']):
            assert row[2]==(case['arrivals'][t-2][0] if t>=2 else 0)
            assert row[3]==(case['arrivals'][t-5][1] if t>=5 else 0)
            booked+=row[2]+row[3]
            if t in (24,48):midnights+=1
        for K in spec['budgets']:
            for label in spec['calendars']:
                for arm,plan in read(source/'outcomes'/f'{s}_{K}_{label}.json.gz').items():
                    x=9;last=0;b=K;cap=0 if arm=='W06_standby_three' else 1 if arm=='W06_one_three' else K
                    nprice=1 if arm=='robust_single' else 3
                    for t,r in enumerate(plan['steps']):
                        own=max(0,cap-(K-b)) if cap<K else b
                        observed[t,own,nprice].append((IX[x,last],r[0],r[9]))
                        x=r[3];last=r[2];b=r[4];checked+=1
                    f=plan['failed']
                    if f and f['t']<72:
                        own=max(0,cap-(K-b)) if cap<K else b
                        observed[f['t'],own,nprice].append((IX[x,last],f['q'],None));failed+=1
        for (t,b,nprice),recs in observed.items():
            start=time.perf_counter();issue=case['issued_H12'][t];H=len(issue)
            per=[];observed_cost=None
            for err in ((-20,0,20) if nprice==3 else (0,)):
                v=np.array([-45000 if stock==9 else BIG for stock,pr in ST]) if t+H==72 else np.array([-6500*stock for stock,pr in ST])
                for l in reversed(range(H)):
                    row=issue[l];p=row[4];h=(l+t)%24;i,qi,j,dg,w=edges[t+l,p,b]
                    price=max(3,row[0]+int(err*min(1,l/4))) if l else row[0]
                    fee=800*(p>0 and (h<6 or 16<=h<22))
                    stage=(row[1]+7*row[2]+4*row[3]+dg)*price*10+w-fee
                    vals=np.where(v[j]<BIG,v[j]+stage,BIG)
                    if l:
                        v=np.full(50,BIG,dtype=np.int64);np.minimum.at(v,i,vals)
                    else:
                        tab=np.full((50,5),BIG,dtype=np.int64);tab[i,qi]=vals;per.append(tab)
                        observed_cost=np.full((50,5),BIG,dtype=np.int64);observed_cost[i,qi]=stage
            for idx,reported,feedback in recs:
                ids=[q for q in range(-2,3) if all(ff[idx,q+2]!=BIG for ff in per)]
                fb=False
                if ids:
                    chosen=min(ids,key=lambda q:(sum(ff[idx,q+2] for ff in per),q))
                else:
                    phys=[q for q in range(-2,3) if observed_cost[idx,q+2]!=BIG]
                    chosen=min(phys,key=lambda q:(observed_cost[idx,q+2]-7000*q,abs(q),q)) if phys else 7
                    fb=bool(phys)
                assert chosen==reported and (feedback is None or bool(feedback)==fb)
            dt=time.perf_counter()-start;worst=max(worst,dt);misses+=int(dt>1);solves+=1
    return dict(reconstructed_completed_nominals=checked,reconstructed_failed_attempts=failed,
                distinct_issued_epoch_budget_price_arm_groups=solves,rolled_midnight_boundaries_checked=midnights,
                verified_booked_jobs=booked,slowest_group_seconds=worst,groups_over_one_second=misses,wall_seconds=time.perf_counter()-torig,
                scope='Independent forecast-only reconstruction. Group timings are batch audit timings, not live device deadline measurements.')
if __name__=='__main__':
    record=audit(Path(sys.argv[1]));Path(sys.argv[2]).write_text(json.dumps(record,indent=2)+'\n');print(record)
