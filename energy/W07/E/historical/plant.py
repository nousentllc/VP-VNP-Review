"""Discrete plant, seeded workload/outage model, and causal issue construction in integer units."""
from pathlib import Path
import gzip
import json
import random

import numpy as np

HERE = Path(__file__).resolve().parent
SEEDS = [69103,69119,69143,69157,69179,69203,69221,69239]
DEV = [61011,61027]
Q = np.arange(-2,3,dtype=np.int64)
SOC = np.repeat(np.arange(2,12,dtype=np.int64),5)
PREV = np.tile(Q,10)
NEXT_SOC = SOC[:,None]+Q
NEXT = (np.clip(NEXT_SOC,2,11)-2)*5+Q+2
INF = 10**12
START = (9-2)*5+2
ROWS = ["price_USD_per_MWh","protected_deciMWh","high_jobs","low_jobs","available_blocks","stranded_floor","up_blocks","down_blocks","optional_up_price_USD"]
DGRID = np.maximum(Q,0)*11+np.minimum(Q,0)*9
WEAR = np.abs(DGRID)*80+np.maximum(0,np.abs(Q)-1)*600
BASIC = (NEXT_SOC>=2)&(NEXT_SOC<=11)&(np.abs(Q-PREV[:,None])<=2)


def save(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    raw=json.dumps(data,separators=(",",":"),allow_nan=False).encode()
    if str(path).endswith(".gz"):
        path.write_bytes(gzip.compress(raw,mtime=0))
    else:
        path.write_text(json.dumps(data,indent=2,allow_nan=False)+"\n")


def read(path):
    return json.loads(gzip.decompress(path.read_bytes()) if str(path).endswith(".gz") else path.read_bytes())


def scheduled(t):
    h=t%24
    return (34 if h<6 else 69 if h<16 else 121 if h<22 else 52,
            20+(4 if 8<=h<20 else 0), int(16<=h<22),int(h<6),
            15 if 15<=h<22 else 4)


def generate(seed,days):
    n=24*days
    rng=random.Random(seed)
    job_rng=random.Random(seed+700001)
    actual=[];jobs=[]; arriving_h=[];arriving_l=[]
    for t in range(n):
        ha=job_rng.choice((0,1,1,1,2))
        la=job_rng.choice((0,0,1,1,2,2))
        arriving_h.append(ha if t+2<n else 0)
        arriving_l.append(la if t+5<n else 0)
    noise=0.;remaining=0;mode=2;spike=0
    for t in range(n):
        normal,protected,up,down,fee=scheduled(t)
        if rng.random()<.025: spike=rng.randint(1,4)
        noise=.68*noise+rng.gauss(0,12)
        price=max(3,min(240,round(normal+noise+(65 if spike>0 else 0))))
        spike=max(0,spike-1)
        if remaining==0 and rng.random()<.04:
            remaining=rng.randint(2,8);mode=rng.choice((0,1))
        pwr=mode if remaining else 2
        remaining=max(0,remaining-1)
        if t>=n-16:pwr=2
        hi=arriving_h[t-2] if t>=2 else 0
        lo=arriving_l[t-5] if t>=5 else 0
        actual.append([price,protected+rng.choice((-2,0,2)),hi,lo,pwr,5 if pwr<2 else 2,
                       min(up,pwr),min(down,pwr),fee])
        jobs.append([arriving_h[t],arriving_l[t]])
    issues=[]
    for t in range(n):
        issue=[actual[t]]
        for k in range(1,min(12,n-t)):
            u=t+k
            normal,base,up,down,fee=scheduled(u)
            power=actual[t][4] if k==1 and u<n-16 else 2
            price=max(3,round(normal+.65**k*(actual[t][0]-scheduled(t)[0])))
            hi=arriving_h[u-2] if 0<=u-2<=t else int(u>=2)
            lo=arriving_l[u-5] if 0<=u-5<=t else int(u>=5)
            issue.append([price,base,hi,lo,power,5 if power<2 else 2,min(up,power),min(down,power),fee])
        issues.append(issue)
    return dict(seed=seed,days=days,columns=ROWS,actual=actual,issued_H12=issues,
                arrival_columns=["high_due_in_2h","low_due_in_5h"],arrivals=jobs)


def stage(row, tariff="variable", trade=False):
    price,protected,high,low,power,locked,up,down,bidfee=row
    fixed=protected+7*high+4*low
    grid=fixed+DGRID
    ok=BASIC&(Q>=-power+up)&(Q<=power-down)&((Q>=0)|(NEXT_SOC>=locked))&(grid>=0)&(grid<=90)
    # Offering an extra unit requires idle upward power and energy above the accessible floor after dispatch.
    bid=(power>0)&(Q-1>=-power+up)&(NEXT_SOC>=locked+1)
    if tariff=="flat":
        cost=grid*500+np.abs(DGRID)*100
    else:
        cost=grid*price*10+WEAR-bid*bidfee*100
    skip=np.zeros_like(bid,dtype=np.int64)
    if trade:
        # Jobs are interchangeable within the low class; dropping them is strictly linear.
        delta=1800-4*price*10
        if delta<0:
            skip=np.minimum(low,np.floor_divide(np.maximum(grid,0),4))[None,:]+np.zeros_like(bid,dtype=np.int64)
            cost=cost+skip*delta
    return np.where(ok,cost,INF),bid,skip


def terminal(fixed=None,credit=50):
    if fixed is None:return -SOC*100*credit
    return np.where(SOC==fixed,-SOC*100*credit,INF)


def back_step(cost,value):
    return np.where((cost<INF)&(value[NEXT]<INF),cost+value[NEXT],INF).min(axis=1)


def terminal_guard(length,target=9):
    # Last 16 hours are publicly outage-free. One-block recovery is permitted at every hour.
    good=[SOC==target]
    reliable=BASIC & (np.abs(Q)<=1)
    for _ in range(16):
        good.append((reliable&good[-1][NEXT]).any(axis=1))
    assert all(good[-1])
    return [good[min(16,length-t)] for t in range(length+1)]
