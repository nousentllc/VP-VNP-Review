"""Independent scalar reserve call and recourse checker; integer Bellman verification over every edge."""
import argparse
import gzip
import json
import hashlib
import statistics as st
import time
from pathlib import Path
import numpy as np
BASE=Path(__file__).resolve().parent
E=BASE.parent
ST=[(s,q) for s in range(2,12) for q in range(-2,3)]
IDX={s:i for i,s in enumerate(ST)};INF=10**12

def read(f):return json.loads(gzip.decompress(f.read_bytes()) if f.suffix==".gz" else f.read_bytes())

def physical(s,p,q,a,load=35):
    if abs(q)>a or abs(q-p)>2 or not 2<=s+q<=11 or q<0 and s+q<(2 if a==2 else 5):return False
    return 0<=load+q*(11 if q>0 else 9)<=90

def make(rows,k,w):
    cache={}
    for t in reversed(range(len(rows))):
        pset=(2,) if t>=len(rows)-16 else (0,1,2)
        c0=[True]*50;c1=c0.copy()
        for p in pset:
            u=min(p,int(16<=t%24<22));d=min(p,int(t%24<6))
            # Both kernel rows influence the feasible graph. Cache common signatures for repeated hours.
            key=(p,u,d,tuple(k[t+1]),tuple(w[t+1]))
            if key not in cache:
                ev=[];rr=[False]*50;br=[False]*50
                for i,(s,prev) in enumerate(ST):
                    for q in range(-2,3):
                        if not -p+u<=q<=p-d or not all(physical(s,prev,q,p,z) for z in (18,48)):continue
                        nx=IDX[s+q,q]
                        if k[t+1][nx]:rr[i]=True
                        if not w[t+1][nx]:continue
                        def activated(command):
                            return all(physical(s,prev,command,p,load) for load in (18,48)) and bool(k[t+1][IDX[s+command,command]])
                        if u and not activated(q-u) or d and not activated(q+d):continue
                        bid=int(p>0 and activated(q-u-1))
                        br[i]=True;ev.append([i,nx,q,bid])
                cache[key]=rr,br,np.asarray(ev,dtype=np.int64).T
            rr,br,_=cache[key]
            c0=[a and b for a,b in zip(rr,c0)];c1=[a and b for a,b in zip(br,c1)]
        assert list(k[t])==c0 and list(w[t])==c1
    return cache


def check(out):
    tic=time.perf_counter_ns();recs=[];by={};g=read(out/'gates.json')
    for spec in g["cases"]:
        s,d=spec["seed"],spec["days"];tag=f"{s}_{d}";pfile=E/'inputs'/f'{tag}.json.gz'
        assert hashlib.sha256(pfile.read_bytes()).hexdigest()==g['inputs_sha256'][tag]
        rows=read(pfile)['actual']
        if d not in by:
            v=read(out/f'kernels_{d}.json.gz');k,w=v['recovery'],v['standby']
            assert k[-1]==w[-1]==[int(s==9) for s,q in ST]
            by[d]=(k,w,make(rows,k,w))
        k,w,cache=by[d];V=read(out/f'certificate_{tag}.json.gz');v=np.array(V['potentials'],dtype=np.int64)
        assert v[-1].tolist()==[-45000 if x==9 else INF for x,y in ST] and v[0,IDX[9,0]]==V['cents']
        assert bool(w[0][IDX[9,0]]) and spec["feasible"]
        online=read(out/f'online_{tag}.json.gz')
        pol={name:dict(idx=IDX[9,0],total=0,up=0,down=0,optional=0,receipts=0,ending=0,steps=0,fallbacks=0,misses=0,msmax=0) for name in online}
        edges=0;optst=IDX[9,0];optcost=0
        for t,(price,facility,hi,lo,a,lock,u,dn,fee) in enumerate(rows):
            assert lock==(2 if a==2 else 5);load=facility+hi*7+lo*4;assert 18<=load<=48
            i,j,q,b=cache[a,u,dn,tuple(k[t+1]),tuple(w[t+1])][2]
            imp=load+q*np.where(q>0,11,9);wear=np.abs(imp-load)*80+600*(np.abs(q)==2)
            cost=imp*price*10+wear-fee*b*100
            cand=np.where(v[t+1,j]<INF,cost+v[t+1,j],INF)
            best=np.full(50,INF,dtype=np.int64);np.minimum.at(best,i,cand)
            assert np.array_equal(best,v[t]);edges+=len(i)
            ix=np.flatnonzero((i==optst)&(cand==v[t,optst]))[0];optst=int(j[ix]);optcost+=int(cost[ix])
            for name,z in pol.items():
                act,after,bid,cents,ns,why=online[name]['actions'][t]
                soc,prev=ST[z['idx']]
                l=np.flatnonzero((i==z['idx']) & (q==act));assert len(l)==1
                ix=l[0];assert int(cost[ix])==cents and int(b[ix])==bid and after==soc+act
                for sign,count in ((-1,u),(1,dn),(-1,u+bid if bid else 0)):
                    if count:
                        command=act+sign*count
                        assert physical(soc,prev,command,a,load) and k[t+1][IDX[soc+command,command]]
                z['idx']=int(j[ix]);z['total']+=cents;z['up']+=u>0;z['down']+=dn>0
                z['optional']+=bid;z['receipts']+=bid*fee;z['ending']=after;z['steps']+=1
                z['fallbacks']+=why is not None;z['misses']+=ns>10**9;z['msmax']=max(z['msmax'],ns/1e6)
        assert ST[optst][0]==9 and optcost-45000==V['cents']
        for name,z in pol.items():
            assert z['ending']==9 and z['total']-45000==online[name]['cents']>=V['cents']
            z['cents']=int(online[name]['cents']);z['wall_s']=online[name]['wall_ns']/1e9
        recs.append(dict(seed=s,days=d,offline_cents=V['cents'],checked_edges=edges,policies=pol))
    summ=[]
    for d in (7,30):
        rows=[r for r in recs if r["days"]==d]
        def mean(fn):return st.mean(fn(r) for r in rows)
        gains=[(r['policies']['scenario']['cents']-r['policies']['continuation']['cents'])/100/d for r in rows]
        summ.append(dict(days=d,all_feasible=len(rows),
            mean_headroom_USD_day={name:mean(lambda r:(r['policies'][name]['cents']-r['offline_cents'])/100/d) for name in pol},
            continuation_gain_vs_price_USD_day=mean(lambda r:(r['policies']['price']['cents']-r['policies']['continuation']['cents'])/100/d),
            continuation_gain_vs_scenario_USD_day=st.mean(gains),range_vs_scenario=[min(gains),max(gains)],n_over_15_vs_scenario=sum(x>15 for x in gains),
            accepted_optional_per_policy={name:sum(r['policies'][name]['optional'] for r in rows) for name in pol},checked_edges=sum(r['checked_edges'] for r in rows)))
    record=dict(panels=summ,by_case=recs,registered_primary_inputs_reused=True,audit_seconds=(time.perf_counter_ns()-tic)/1e9)
    (out/'audit.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(summ))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,default=BASE/'results');check(p.parse_args().out)
