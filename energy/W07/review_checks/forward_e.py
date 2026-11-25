"""Read-only E review; never imports the production or E audit modules."""
import argparse, gzip, json
from pathlib import Path
from collections import defaultdict
from fractions import Fraction
DEFAULT_RESULTS=Path('E/results')
def read(path):
    return json.loads(gzip.decompress(path.read_bytes()) if path.suffix=='.gz' else path.read_bytes())
def schedule(t):
    hour=t%24
    return [(34 if hour<6 else 69 if hour<16 else 121 if hour<22 else 52),
            20+4*(8<=hour<20),int(16<=hour<22),int(hour<6),(15 if 15<=hour<22 else 4)]
def check_issues(panel):
    count=0
    for t,issue in enumerate(panel['issued_H12']):
        current=panel['actual'][t]
        assert issue[0]==current
        for k,row in enumerate(issue[1:],1):
            u=t+k
            norm,base,up,down,fee=schedule(u)
            price=max(3,round(norm+0.65**k*(current[0]-schedule(t)[0])))
            p=current[4] if k==1 and u<56 else 2
            bookings=panel['arrivals'][:t+1]
            h=(bookings[u-2][0] if 0<=u-2<len(bookings) else int(u>=2))
            l=(bookings[u-5][1] if 0<=u-5<len(bookings) else int(u>=5))
            assert row==[price,base,h,l,p,5 if p<2 else 2,min(up,p),min(down,p),fee]
            count+=1
    return count
def cash(row,a,c,t):
    price,firm,h,l,p,*_=row
    load=firm+7*h+4*l
    move=a*(11 if a>=0 else 9)
    return (load+move)*price*10+abs(move)*80+600*(abs(a)==2)-800*(p>0 and (t%24<6 or 16<=t%24<22))-350*(c!=0)
def trans(s,prev,q,p,c,load,d):
    if not -p+int(d<0)<=q<=p-int(d>0):return None
    for a in (q,q+c):
        after=s+a
        if not (2<=after<=11 and abs(a-prev)<=2 and abs(a)<=p and
                (a>=0 or after>=(2 if p==2 else 5)) and 0<=load+a*(11 if a>=0 else 9)<=90):return None
    return s+q+c,q+c
def fwd(rows,K,calendar,mask):
    reached={(9,0):0};b=K
    for t,row in enumerate(rows):
        p=row[4];load=row[1]+7*row[2]+4*row[3]
        d=(int(t%24<6)-int(16<=t%24<22)) if p else 0
        c=d if b and t in calendar else 0
        nxt={}
        for (s,prev),val in reached.items():
            for q in (-2,-1,0,1,2):
                if mask is not None and not mask[t][p][b][(s-2)*5+prev+2][q+2]:continue
                v=trans(s,prev,q,p,c,load,d)
                if v is not None:
                    z=val+cash(row,q+c,c,t)
                    if v not in nxt or z<nxt[v]:nxt[v]=z
        reached=nxt;b-=int(bool(c))
    return min(v-45000 for (s,p),v in reached.items() if s==9)
def main(results):
    root=Path(results)
    design=read(root/'design.json');gates=read(root/'gates.json')['cases']
    kernel=read(root/'kernels.json.gz')['actions'];stats=defaultdict(list)
    groups=defaultdict(set); checked=0;count=0;steps=0
    counter=[];demand=[];protected_jobs=0;fallback=0
    for seed in design['seeds']:
        panel=read(root/'inputs'/f'{seed}.json.gz');count+=check_issues(panel)
        actual=panel['actual'];arrivals=panel['arrivals']
        for t,row in enumerate(actual):
            assert row[2]==(arrivals[t-2][0] if t>=2 else 0) and row[3]==(arrivals[t-5][1] if t>=5 else 0)
            demand.append(row[1]+7*row[2]+4*row[3])
        for K in design['budgets']:
            for name,cal in design['calendars'].items():
                gate=next(z for z in gates if (z['seed'],z['K'],z['calendar'])==(seed,K,name))
                floor=fwd(actual,K,cal,kernel);weak=fwd(actual,K,cal,None)
                assert floor==gate['oracle'] and weak<=floor
                if weak<floor:counter.append(dict(seed=seed,K=K,cal=name,L=floor,unshielded=weak))
                arms=read(root/'outcomes'/f'{seed}_{K}_{name}.json.gz')
                for arm,p in arms.items():
                    s=9;prev=0;b=K;net=-45000
                    for t,step in enumerate(p['steps']):
                        groups[(arm,seed,K,t,s,prev,b)].add(step[0])
                        q,c,a,snew,bnew,*cashrow=step
                        x=actual[t]; expected=(int(t%24<6)-int(16<=t%24<22)) if t in cal and x[4] and b else 0
                        assert expected==c and a==q+c and snew==s+a and bnew==b-int(bool(c))
                        st=cash(x,a,c,t);net+=st;assert st==sum(cashrow[:4])
                        s,prev,b=snew,a,bnew;steps+=1
                        if arm=='robust_three':fallback+=cashrow[4]
                    if p['failed'] is None:assert s==9 and p['net_cents']==net
                    else: assert p['net_cents'] is None
                assert arms['robust_three']['net_cents']==gate['baseline']
                stats[K].append((gate['baseline']-floor,arms['robust_three']['net_cents']-arms['robust_single']['net_cents']))
                assert gate['excludes_15_per_day']==(gate['baseline']-floor<4500)
                checked+=1
    assert max(map(len,groups.values()))==1
    return dict(cases=checked,issued_future_rows=count,immediate_rows=len(design['seeds'])*72,ledger_hours=steps,
                policy_key_count=len(groups),load_observed=[min(demand),max(demand)],robust_three_fallback_hours=fallback,
                per_budget={K:dict(gain_USD_day=str(sum(Fraction(y,300) for x,y in vs)/len(vs)),
                                    ceiling_USD_day=str(sum(Fraction(x,300) for x,y in vs)/len(vs)),excluded=sum(x<4500 for x,y in vs))
                            for K,vs in stats.items()},looser_path_floor_diff=len(counter),
                strongest_scope_counterexample=max(counter,key=lambda c:c['L']-c['unshielded']) if counter else None)
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--results', type=Path, default=DEFAULT_RESULTS,
                        help='Released E/results directory (default: relative to W07 root)')
    print(json.dumps(main(parser.parse_args().results),indent=2))
