"""Exact sufficient redundancy test for the implemented absolute angle boxes."""
import argparse
import heapq
import json
import re
from fractions import Fraction as Q
from pathlib import Path

HERE=Path(__file__).resolve().parent
def cells(text,key):
    pattern=r'\bmpc\.'+key+r'\s*=\s*\[([^\]]*)\]'
    return [r.split() for r in re.search(pattern,text,re.S)[1].split(';') if r.strip()]

def distances(adj,source):
    dist={source:Q(0)};queue=[(Q(0),source)]
    while queue:
        value,v=heapq.heappop(queue)
        if value!=dist[v]:continue
        for key,length in adj[v]:
            if length<0:raise ValueError('Dijkstra requires nonnegative edge lengths')
            alt=value+length
            if key not in dist or alt<dist[key]:
                dist[key]=alt;heapq.heappush(queue,(alt,key))
    return dist
def item(path):
    text='\n'.join(line.partition('%')[0] for line in path.read_text().splitlines())
    buses=cells(text,'bus');branches=cells(text,'branch')
    ids=[int(row[0]) for row in buses];ref=[int(row[0]) for row in buses if int(row[1])==3]
    assert len(ref)==1 and len(set(ids))==len(ids)
    adj={k:[] for k in ids};rev={k:[] for k in ids}
    for row in branches:
        if Q(row[10])<=0:continue
        i,j=int(row[0]),int(row[1]);lo,hi=Q(row[11]),Q(row[12])
        if lo>0 or hi<0:
            return dict(case=path.stem,status='mixed-sign directed edge lengths require another shortest-path method')
        for a,b,w in [(j,i,hi),(i,j,-lo)]:
            adj[a].append((b,w));rev[b].append((a,w))
    upper=distances(adj,ref[0]);minus_lower=distances(rev,ref[0])
    assert len(upper)==len(ids)==len(minus_lower)
    unknown=[i for i in ids if max(upper[i],minus_lower[i])>360]
    return dict(case=path.stem,reference_bus=ref[0],buses=len(ids),unproved_buses=unknown,
        certified_redundant=not unknown,max_upper_deg=str(max(upper.values())),min_lower_deg=str(-max(minus_lower.values())),
        bounds_deg={str(i):[str(-minus_lower[i]),str(upper[i])] for i in ids})
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--inputs',type=Path,default=HERE/'inputs');p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();rows=[item(f) for f in sorted(a.inputs.glob('*.m'))]
    a.out.write_text(json.dumps(dict(scope='Exact directed path bounds from original active branch angle limits in degrees and zero reference angle.',cases=rows),indent=2)+'\n')
