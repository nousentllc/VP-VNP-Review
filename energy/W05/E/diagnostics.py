"""Secondary Pareto trade-offs and checks on equivalence between nested policies."""
import argparse,csv,json,math
from pathlib import Path
from collections import defaultdict
import numpy as np
from audit import write,save,read
ROOT=Path(__file__).resolve().parent

def diagnostics(folder):
    folder=Path(folder)
    rows=list(csv.DictReader((folder/'scenario_metrics.csv').open()))
    summary=list(csv.DictReader((folder/'arm_summary.csv').open()))
    indexed={(r['panel'],r['arm']):r for r in summary if r['regime']=='all' and r['arm']!='offline'}
    pareto=[];eq=[]
    for (panel,arm),r in indexed.items():
        names=['mean_shed','mean_imports','mean_throughput','cvar90','mean_terminal']
        def vec(s):return np.array([float(s[x]) for x in names])*np.array([1,1,1,1,-1])
        current=vec(r)
        dominating=[name for (p,name),b in indexed.items() if p==panel and np.all(vec(b)<=current+1e-6) and np.any(vec(b)<current-1e-6)]
        pareto.append(dict(panel=panel,arm=arm,pareto_efficient=not bool(dominating),dominated_by='|'.join(dominating),
              **{key:r[key] for key in names}))
    for panel in ['primary','alternative']:
        index={(x['case'],x['arm']):x for x in rows if x['panel']==panel}
        ids=sorted({k[0] for k in index})
        for a,b in [('nested6','learned6'),('nestedrule6','rule6'),('fixed12','learned12'),('rule12','rule3')]:
            common=[case for case in ids if (case,a) in index and (case,b) in index]
            ds=[abs(float(index[case,a]['shed'])-float(index[case,b]['shed'])) for case in common]
            eq.append(dict(panel=panel,arm=a,comparator=b,common_days=len(common),unequal_realized_shedding=sum(d>1e-6 for d in ds),max_abs_delta=max(ds)))
    write(folder/'pareto.csv',pareto);write(folder/'nested_checks.csv',eq)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);args=p.parse_args();diagnostics(args.out)
