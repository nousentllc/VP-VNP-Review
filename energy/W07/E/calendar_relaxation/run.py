"""Exploratory lower bound: reveal all future exogenous prices/loads/powers but keep call calendar hidden."""
from pathlib import Path
import sys
import time
import numpy as np
BASE=Path(__file__).resolve().parents[1];sys.path.insert(0,str(BASE))
from model import read,save,endpoint,components,Q,SOC,START,INF,traces


def solve(rows,K,calendars,mask):
    posts=[traces(rows,K,c)[1] for c in calendars]
    classes=[{tuple(range(len(posts)))}]
    for t in range(len(rows)):
        after=set()
        for group in classes[-1]:
            for c in set(posts[i][t] for i in group):
                after.add(tuple(i for i in group if posts[i][t]==c))
        classes.append(after)
    following={g:np.where(SOC==9,-45000*len(g),INF) for g in classes[-1]};saved=[]
    for t in reversed(range(len(rows))):
        vals={};step=[]
        for group in sorted(classes[t]):
            b=K-sum(c!=0 for c in posts[group[0]][:t])
            p=rows[t][4];good=mask[t,p,b].copy();score=np.zeros((50,5),dtype=np.int64)
            for c in sorted(set(posts[i][t] for i in group)):
                g=tuple(i for i in group if posts[i][t]==c);next_values=following[g][endpoint(Q+c)]
                good &= next_values<INF;score+=len(g)*sum(components(rows[t],Q+c,c,t))+next_values
            valid=np.where(good,score,INF)
            vals[group]=valid.min(axis=1)
            step.append(dict(group=list(group),V=vals[group].tolist(),
                    witness=np.where(good.any(axis=1),np.argmin(valid,axis=1)-2,8).tolist()))
        saved.append(step);following=vals
    return int(following[tuple(range(len(posts)))][START]),saved[::-1]


def run(source,out):
    d=read(source/'design.json')
    # Preserve the serialized calendar order rather than reading policy results.
    names=list(d['calendars']);cals=[d['calendars'][n] for n in names]
    mask=np.array(read(source/'kernels.json.gz')['actions'],dtype=bool)
    ti=time.perf_counter();records=[]
    for seed in d['seeds']:
        rows=read(source/'inputs'/f'{seed}.json.gz')['actual']
        for K in d['budgets']:
            value,tables=solve(rows,K,cals,mask)
            save(out/f'{seed}_{K}.json.gz',dict(calendars=names,value_sum_cents=value,scheme='sum over original four equally weighted calendars',tables=tables))
            records.append([seed,K,value])
    save(out/'run.json',dict(rows=records,wall_seconds=time.perf_counter()-ti))

if __name__=='__main__':run(Path(sys.argv[1]),Path(sys.argv[2]))
