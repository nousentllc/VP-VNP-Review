"""Integer robust physical model; cost cents and energy in internal one-hour MWh blocks."""
from pathlib import Path
import sys
import numpy as np
BASE=Path(__file__).resolve().parent
sys.path.insert(0,str(BASE/'historical'))
from plant import SOC, PREV, Q, NEXT, DGRID, WEAR, INF, START, generate, save, read

SEEDS=(73091,73127,73171,73217,73261,73303,73347,73391,73433,73477,73519,73561)
BUDGETS=(0,1,2,4)
N=72
# Dispatcher will request at these hidden times, truncate only delivered events at remaining budget.
CALENDARS={'standby':(), 'dawn':(4,5,28,29), 'peak':(18,19,42,43), 'mixed':(5,16,29,40)}
OFFERS=(0,1,2) # observed inverter limits
FEE=800 # cents per contracted availability hour
ACTIVATION=350 # cents per delivered one-hour internal block


def direction(t):
    return int(t%24<6)-int(16<=t%24<22)


def powers(t,n):
    return (2,) if t>=n-16 else OFFERS


def physical(s,prev,act,power,load):
    after=s+act
    response=np.where(act>0,11*act,9*act)
    return ((np.abs(act)<=power)&(np.abs(act-prev)<=2)&(after>=2)&(after<=11)&
            ((act>=0)|(after>= (2 if power==2 else 5)))&(load+response>=0)&(load+response<=90))


def endpoint(act):
    return (np.clip(SOC[:,None]+act,2,11)-2)*5+np.clip(act,-2,2)+2


def kernels(n,max_budget,signs=None,availability=None):
    signs=[direction(t) for t in range(n)] if signs is None else signs
    availability=[powers(t,n) for t in range(n)] if availability is None else availability
    v=np.zeros((n+1,max_budget+1,50),dtype=bool); v[-1]=SOC==9
    mask=np.zeros((n,3,max_budget+1,50,5),dtype=bool)
    for t in reversed(range(n)):
        for p in availability[t]:
            d=signs[t] if p else 0
            def okay(a):return physical(SOC[:,None],PREV[:,None],a,p,18)&physical(SOC[:,None],PREV[:,None],a,p,48)
            nom=okay(Q)&(Q>=-p+int(d<0))&(Q<=p-int(d>0))
            for b in range(max_budget+1):
                good=nom&v[t+1,b,NEXT]
                if b and d:
                    good=good&okay(Q+d)&v[t+1,b-1,endpoint(Q+d)]
                mask[t,p,b]=good
        v[t]=np.logical_and.reduce([mask[t,p].any(axis=-1) for p in availability[t]])
    return v,mask


def components(row,act,c,t):
    price,f,h,l,p,_,_,_,_=row
    load=f+7*h+4*l
    move=11*np.maximum(act,0)+9*np.minimum(act,0)
    import_deci=load+move
    return import_deci*price*10,abs(move)*80+600*(abs(act)==2),-FEE*int(p>0 and direction(t)!=0),-ACTIVATION*int(c!=0)


def signal(t,p,b,calendar):
    return direction(t) if t in calendar and p and b else 0


def traces(rows,K,calendar):
    remaining=K; budgets=[];calls=[]
    for t,row in enumerate(rows):
        budgets.append(remaining); c=signal(t,row[4],remaining,calendar)
        calls.append(c);remaining-=int(c!=0)
    return budgets,calls


def oracle(rows,K,calendar,mask):
    # Full chronology/calls are revealed only to this relaxed comparison.
    budgets,calls=traces(rows,K,calendar)
    v=np.where(SOC==9,-45000,INF); hist=[v.tolist()]
    for t in reversed(range(len(rows))):
        row=rows[t];b=budgets[t];c=calls[t];act=Q+c
        step=sum(components(row,act,c,t)); nx=endpoint(act)
        cand=np.where(mask[t,row[4],b]&(v[nx]<INF),step+v[nx],INF)
        v=cand.min(axis=1);hist.append(v.tolist())
    return int(v[START]),hist[::-1]


def price_table(panel,mask,scenarios,states_budget):
    """W06 shared first action; three issued price offsets, separate future forecast recourse and fixed marks."""
    T=len(panel['issued_H12'])
    result=np.zeros((T,states_budget+1,50),dtype=np.int8)
    fallback=np.zeros_like(result,dtype=bool)
    for t,issue in enumerate(panel['issued_H12']):
        h=len(issue)
        for b in range(states_budget+1):
            score=np.zeros((50,5),dtype=np.int64)
            active=mask[t,issue[0][4],b].copy()
            first=sum(components(issue[0],Q,0,t))
            for err in scenarios:
                v=np.where(SOC==9,-45000,INF) if t+h==T else -6500*SOC
                for k in reversed(range(1,h)):
                    row=issue[k].copy()
                    row[0]=max(3,row[0]+int(err*min(1,k/4)))
                    m=mask[t+k,row[4],b]
                    cost=sum(components(row,Q,0,t+k))
                    v=np.where(m&(v[NEXT]<INF),cost+v[NEXT],INF).min(axis=1)
                active &= v[NEXT]<INF
                score+=first+v[NEXT]
            allowed=mask[t,issue[0][4],b]
            safe=np.argmin(np.where(allowed,(first-Q*7000)*100+np.abs(Q)*10+Q+2,INF),axis=1)
            hit=~active.any(axis=1)
            pick=np.where(hit,safe,np.argmin(np.where(active,score,20*INF),axis=1))
            result[t,b]=np.where(allowed.any(axis=1),pick-2,7)
            fallback[t,b]=hit&allowed.any(axis=1)
    return result,fallback


def simulate(panel,K,calendar,table,cap,baseline_label):
    s=9;prev=0;b=K;acts=[];expense=[0]*4;failure=None
    for t,row in enumerate(panel['actual']):
        state=(s-2)*5+prev+2
        # One-call and standby competitors are deliberately unshielded beyond their own guarantees.
        own_b=max(0,cap-(K-b)) if cap<K else b
        q=int(table[0][t,own_b,state]); c=signal(t,row[4],b,calendar)
        a=q+c;p=row[4];load=row[1]+7*row[2]+4*row[3];d=direction(t) if p else 0
        if q==7 or not physical(s,prev,q,p,load) or not -p+int(d<0)<=q<=p-int(d>0) or not physical(s,prev,a,p,load):
            failure=dict(t=t,s=s,prev=prev,b=b,p=p,q=q,call=c,attempted=a);break
        items=[int(z) for z in components(row,a,c,t)]
        expense=[x+y for x,y in zip(expense,items)];b-=int(c!=0);s+=a;prev=a
        acts.append([q,c,a,s,b,*items,int(table[1][t,own_b,state])])
    if not failure and s!=9:failure=dict(t=len(acts),s=s,reason='terminal')
    return dict(arm=baseline_label,steps=acts,failed=failure,closing_soc=s,remaining=b,subtotal_cents=expense,
                net_cents=None if failure else sum(expense)-45000)
