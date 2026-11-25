"""Independent scalar Bellman and witness checker with call-history grouping reconstructed from raw calendars."""
import gzip
import json
import statistics
import sys
import time
from collections import defaultdict
from fractions import Fraction as F
from itertools import product
from pathlib import Path

ST=list(product(range(2,12),range(-2,3)));IDX={s:i for i,s in enumerate(ST)}
INF=10**12

def read(p):return json.loads(gzip.decompress(p.read_bytes()) if p.suffix=='.gz' else p.read_bytes())

def check(src,out):
    start=time.perf_counter()
    m=read(src/'kernels.json.gz')['actions'];spec=read(src/'design.json')
    orig=read(src/'gates.json')['cases'];panels=[];edges=0;branches=0
    for seed in spec['seeds']:
        rows=read(src/'inputs'/f'{seed}.json.gz')['actual'];T=len(rows)
        for K in spec['budgets']:
            cert=read(out/f'{seed}_{K}.json.gz'); names=cert['calendars'];assert set(names)==set(spec['calendars'])
            histories=[]
            for label in names:
                path=[];b=K
                for t,row in enumerate(rows):
                    direction=int(t%24<6)-int(16<=t%24<22)
                    c=direction if row[4] and b and t in spec['calendars'][label] else 0
                    b-=int(bool(c));path.append(c)
                histories.append(tuple(path))
            layers=[]
            for t in range(T+1):
                found=defaultdict(list)
                for i,h in enumerate(histories):found[h[:t]].append(i)
                layers.append(found)
            next_vals={tuple(g):[-45000*len(g) if s==9 else INF for s,p in ST] for g in layers[T].values()}
            for t in reversed(range(T)):
                row=rows[t];speed=row[4];load=row[1]+7*row[2]+4*row[3]
                d=int(t%24<6)-int(16<=t%24<22)
                stored={tuple(b['group']):b for b in cert['tables'][t]}
                assert set(stored)==set(tuple(v) for v in layers[t].values())
                for hist,g in layers[t].items():
                    witness=stored[tuple(g)];b=K-sum(map(bool,hist))
                    splits={c:tuple(layers[t+1][hist+(c,)]) for c in set(histories[i][t] for i in g)}
                    for i,(s,prev) in enumerate(ST):
                        offers={}
                        for col,allowed in enumerate(m[t][speed][b][i]):
                            if not allowed:continue
                            q=col-2;net=0;okay=True
                            for c,children in splits.items():
                                a=q+c;after=s+a;dg=a*(11 if a>0 else 9);j=IDX[after,a]
                                val=next_vals[children][j];branches+=1
                                if val==INF:okay=False;break
                                cost=(load+dg)*row[0]*10+abs(dg)*80+600*int(abs(a)==2)-800*int(bool(d) and speed>0)-350*int(c!=0)
                                net+=len(children)*cost+val
                            if okay:offers[q]=net
                            edges+=1
                        best=min(offers.values(),default=INF);chosen=witness['witness'][i]
                        assert best==witness['V'][i] and ((not offers and chosen==8) or offers[chosen]==best)
                next_vals={g:z['V'] for g,z in stored.items()}
            val=next_vals[tuple(range(4))][IDX[9,0]];assert val==cert['value_sum_cents']
            baselines=sum(r['baseline'] for r in orig if (r['seed'],r['K'])==(seed,K));pf=sum(r['oracle'] for r in orig if (r['seed'],r['K'])==(seed,K))
            assert pf<=val<=baselines
            panels.append(dict(seed=seed,K=K,baseline_sum=baselines,PF_sum=pf,partial_sum=val,
                reduction_USD_per_site_day=(val-pf)/1200,remaining_USD_per_site_day=(baselines-val)/1200,excludes=(baselines-val)<18000))
    agg=[]
    for K in spec['budgets']:
        r=[x for x in panels if x['K']==K]
        agg.append(dict(K=K,mean_PF_ceiling_USD_day=statistics.mean((z['baseline_sum']-z['PF_sum'])/1200 for z in r),
            mean_partial_ceiling_USD_day=statistics.mean(z['remaining_USD_per_site_day'] for z in r),
            hidden_calendar_tightening_USD_day=statistics.mean(z['reduction_USD_per_site_day'] for z in r),exclusions_over_seed_means=sum(z['excludes'] for z in r)))
    record=dict(groups=agg,panels=panels,branches=branches,edges=edges,checker_seconds=time.perf_counter()-start)
    (out/'check.json').write_text(json.dumps(record,indent=2)+'\n')
    return agg
if __name__=='__main__':print(check(Path(sys.argv[1]),Path(sys.argv[2])))
