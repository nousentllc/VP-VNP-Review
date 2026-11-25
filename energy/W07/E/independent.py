"""Scalar physics and independent AND/OR tree plus Bellman residual checks. Does not import model.py."""
import gzip
import itertools
import json
import sys
from functools import lru_cache
from pathlib import Path
import time
import numpy as np

ST=list(itertools.product(range(2,12),range(-2,3)))
IX={x:i for i,x in enumerate(ST)}
BIG=10**12


def read(f):
    return json.loads(gzip.decompress(f.read_bytes()) if f.suffix=='.gz' else f.read_bytes())


def sign(t):return 1 if t%24<6 else -1 if 16<=t%24<22 else 0


def admits(s,prev,a,p):
    if abs(a)>p or abs(prev-a)>2 or not 2<=s+a<=11:return False
    if a<0 and s+a< (2 if p==2 else 5):return False
    dg=a*(9 if a<0 else 11)
    return 18+dg>=0 and 48+dg<=90


@lru_cache(None)
def branches(state,p,d):
    s,prev=ST[state]; pairs=[]
    for q in range(-2,3):
        if not admits(s,prev,q,p):continue
        if q+max(d,0)>p or q+min(d,0)<-p:continue
        j=IX[s+q,q]
        a=q+d
        alt=IX[s+a,a] if admits(s,prev,a,p) else None
        pairs.append((q,j,alt))
    return pairs


def small_forward(signs,ps,b,state):
    # Explicit game tree without memoizing viability values. Terminal feasibility tested only at leaves.
    if not signs:return ST[state][0]==9
    for power in ps[0]:
        d=signs[0] if power else 0
        for q,j,j1 in branches(state,power,d):
            if not small_forward(signs[1:],ps[1:],b,j):continue
            if d and b and (j1 is None or not small_forward(signs[1:],ps[1:],b-1,j1)):continue
            break
        else:return False
    return True


def verified_graph(k,mask_record,n):
    checked=0; counts=[0]*5
    edges={}
    for t in reversed(range(n)):
        possible=(2,) if t>=n-16 else (0,1,2)
        for b in range(5):
            intersection=[True]*50
            for p in possible:
                d=sign(t) if p else 0
                # Cache exact verified edges by the two continuation-set signatures.
                key=(p,d,b>0,tuple(k[t+1][b]),tuple(k[t+1][max(0,b-1)]))
                if key not in edges:
                    keep=[]
                    for i in range(50):
                        for q,j,alt in branches(i,p,d):
                            if not k[t+1][b][j]:continue
                            if d and b and (alt is None or not k[t+1][b-1][alt]):continue
                            keep.append((i,q,j,alt if d and b else j))
                    edges[key]=np.asarray(keep,dtype=np.int64).reshape(-1,4).T
                i,q,j,alt=edges[key]
                bits=np.zeros((50,5),dtype=bool);bits[i,q+2]=True
                assert np.array_equal(bits,mask_record[t,p,b])
                intersection=np.logical_and(intersection,bits.any(axis=1)); checked+=len(i)
            assert np.array_equal(intersection,k[t][b]); counts[b]+=sum(intersection)
    for t in range(n+1):
        assert all(np.all(np.asarray(k[t][b])<=np.asarray(k[t][b-1])) for b in range(1,5))
    assert all(k[-1][b]==[soc==9 for soc,q in ST] for b in range(5))
    return edges,checked,list(map(int,counts))


def check(root):
    timer=time.perf_counter()
    rec=read(root/'kernels.json.gz');k=rec['values'];m=np.asarray(rec['actions'],dtype=bool)
    n=len(k)-1;edges,checks,counts=verified_graph(k,m,n)
    small=read(root/'small_kernels.json')
    small_n=0
    for spec in small:
        for b in range(5):
            for i in range(50):
                assert bool(spec['root'][b][i])==small_forward(spec['directions'],spec['available'],b,i)
                small_n+=1
    cert_edges=0; simulations=0;verify_actions=0;losses=0
    gate=read(root/'gates.json')
    by_case={(r['seed'],r['K'],r['calendar']):r for r in gate['cases']}
    design=read(root/'design.json')
    for seed in design['seeds']:
        case=read(root/'inputs'/f'{seed}.json.gz');rows=case['actual']
        # Reconstruct the issue using only features that existed by the decision clock.
        for t,issue in enumerate(case['issued_H12']):
            assert issue[0]==rows[t] and len(issue)==min(12,n-t)
            for l,row in enumerate(issue[1:],1):
                u=t+l;h=u%24
                def normal(h):return 34 if h<6 else 69 if h<16 else 121 if h<22 else 52
                power=rows[t][4] if l==1 and u<n-16 else 2
                def booked(delay,col):return case['arrivals'][u-delay][col] if 0<=u-delay<=t else int(u>=delay)
                pred=[max(3,round(normal(h)+.65**l*(rows[t][0]-normal(t%24)))),20+4*(8<=h<20),
                      booked(2,0),booked(5,1),power,5 if power<2 else 2,min(power,int(sign(u)<0)),min(power,int(sign(u)>0)),15 if 15<=h<22 else 4]
                assert pred==row
        for K in design['budgets']:
            for lab,cal in design['calendars'].items():
                cert=read(root/'certificates'/f'{seed}_{K}_{lab}.json.gz')
                v=np.asarray(cert['values'],dtype=np.int64)
                assert v[-1].tolist()==[-45000 if s==9 else BIG for s,p in ST]
                b=K
                for t,row in enumerate(rows):
                    price,facility,h,l,p,lock,u,dn,fee=row; load=facility+7*h+4*l; d=sign(t) if p else 0
                    assert 18<=load<=48 and lock==(2 if p==2 else 5) and (u,dn)==(int(d<0),int(d>0))
                    c=d if b and t in cal else 0
                    i,q,j,alt=edges[p,d,b>0,tuple(k[t+1][b]),tuple(k[t+1][max(b-1,0)])]
                    a=q+c; nxt=alt if c else j
                    dg=np.where(a>0,11*a,9*a)
                    cost=(load+dg)*price*10+np.abs(dg)*80+600*(np.abs(a)==2)-800*(d!=0)-350*(c!=0)
                    trial=np.where(v[t+1,nxt]<BIG,cost+v[t+1,nxt],BIG)
                    best=np.full(50,BIG,dtype=np.int64);np.minimum.at(best,i,trial)
                    assert np.array_equal(best,v[t])
                    b-=int(c!=0);cert_edges+=len(i)
                g=by_case[seed,K,lab]
                assert g['oracle']==int(v[0,IX[9,0]]) and g['baseline']>=g['oracle']
                path=read(root/'outcomes'/f'{seed}_{K}_{lab}.json.gz')
                for name,plan in path.items():
                    simulations+=1;s=9;p0=0;b=K;total=0
                    limit=0 if name=='W06_standby_three' else 1 if name=='W06_one_three' else K
                    for t,record in enumerate(plan['steps']):
                        q,c,a,after,rem,energy,wear,standby,activation,fb=record
                        row=rows[t];speed=row[4];d=sign(t) if speed else 0
                        assert c==(d if b and t in cal else 0)
                        own=max(0,limit-(K-b)) if limit<K else b
                        assert m[t,speed,own,IX[s,p0],q+2] and a==q+c and admits(s,p0,a,speed)
                        load=row[1]+7*row[2]+4*row[3]; dg=a*(11 if a>0 else 9)
                        assert energy==(load+dg)*row[0]*10 and wear==abs(dg)*80+600*(abs(a)==2)
                        assert (standby,activation)==(-800*int(d!=0),-350*int(c!=0))
                        s+=a;p0=a;b-=int(bool(c));assert (s,b)==(after,rem)
                        total+=energy+wear+standby+activation;verify_actions+=1
                    f=plan['failed']
                    if f:
                        losses+=1;t=f['t']
                        if t<n:
                            q=f['q']; speed=rows[t][4];d=sign(t) if speed else 0
                            c=d if b and t in cal else 0
                            assert f['s']==s and f['prev']==p0 and f['b']==b and f['call']==c
                            own=max(0,limit-(K-b)) if limit<K else b
                            assert (q==7 and not any(m[t,speed,own,IX[s,p0]])) or not admits(s,p0,q+c,speed)
                        else:assert s!=9
                        assert plan['net_cents'] is None
                    else:
                        assert len(plan['steps'])==n and s==9 and plan['net_cents']==total-45000
                    if name=='robust_three':assert not f and plan['net_cents']==g['baseline']
                    if name.startswith('robust'): assert not f and total-45000>=g['oracle']
    result=dict(long_admissible_edges=checks,viable_state_hours_by_budget=counts,independent_full_small_tree_root_states=small_n,
                oracle_edges=cert_edges,simulations=simulations,actual_commands=verify_actions,failed_trajectories=losses,seconds=time.perf_counter()-timer)
    (root/'independent.json').write_text(json.dumps(result,indent=2)+'\n')
    return result

if __name__=='__main__':print(check(Path(sys.argv[1])))
