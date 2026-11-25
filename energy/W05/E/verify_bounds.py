"""Solver-free, independent exact arithmetic verification of offline opportunity bounds."""
import argparse,copy,gzip,json
from fractions import Fraction as F
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def exact(t):return F(float(t))
def parse(t):return F(t[0],t[1])
def verify(c,p,record,with_weights=False):
    if c['id']!=record['case']:raise ValueError('case identity')
    y=[parse(z) for z in record['eq_multipliers']];z=[parse(q) for q in record['le_multipliers']]
    if len(y)!=48 or len(z)!=48 or max(z)>0:raise ValueError('dual sign or dimension')
    prime=[[parse(x) for x in h] for h in record['primal']]
    if len(prime)!=24 or any(len(h)!=5 for h in prime):raise ValueError('dimensions')
    ec=exact(p['eta_c']);dr=exact(1./p['eta_d'])
    cap=exact(p['energy']);initial=exact(p['initial']);previous=exact(p['previous'])
    reduced=[F(i%5==3) for i in range(120)]
    constant=F(0);cost=F(0);last_e=initial;last_g=previous;bounds=[]
    for t,(g,ch,ds,u,e) in enumerate(prime):
        load=exact(c['load'][t]);floor=exact(c['floor'][t]);power=p['power']*bool(c['available'][t])
        hi=[exact(p['grid_cap']),exact(power),exact(max(0.,power-c['reserve'][t])),exact(c['load'][t]-p['facility']),cap]
        lo=[F(0),F(0),F(0),F(0),floor]
        if any(not a<=v<=b for a,v,b in zip(lo,prime[t],hi)):raise ValueError('primal bounds')
        if g-ch+ds+u!=load or e!=last_e+ec*ch-dr*ds or ds*ch!=0 or abs(g-last_g)>exact(p['ramp']):
            raise ValueError('physical constraints')
        cost+=u;last_e=e;last_g=g;bounds.extend(zip(lo,hi))
        # c - M' dual. Rebuild each incidence without the optimization library or generator.
        j=5*t;yb,ys=y[2*t:2*t+2];up,down=z[2*t:2*t+2]
        constant+=yb*load+ys*(initial if t==0 else 0)
        constant+=up*exact(p['ramp']+(p['previous'] if t==0 else 0))+down*exact(p['ramp']-(p['previous'] if t==0 else 0))
        reduced[j]-=yb+up-down;reduced[j+1]+=yb+ys*ec
        reduced[j+2]-=yb+ys*dr;reduced[j+3]-=yb;reduced[j+4]-=ys
        if t:
            reduced[j-5]+=up-down
            reduced[j-1]+=ys
    lower=constant+sum(r*(l if r>=0 else u) for r,(l,u) in zip(reduced,bounds))
    if cost!=parse(record['upper']) or lower!=parse(record['lower']) or cost-lower!=parse(record['gap']) or cost<lower:
        raise ValueError('bound identity')
    if with_weights:
        return cost-lower,sum(abs(q) for q in y+z+reduced)
    return cost-lower

def run(records,out):
    panel=json.loads(gzip.decompress((ROOT/'inputs/holdout.json.gz').read_bytes()))
    certs=json.loads(gzip.decompress(Path(records).read_bytes()))
    by={r['case']:r for r in certs};cases=panel['cases'];p=panel['parameters'];by_panel={}
    if len(by)!=len(certs) or len(by)!=len(cases):raise ValueError('certificate count')
    for c in cases:
        gap=verify(c,p,by[c['id']]);by_panel.setdefault(c['panel'],[]).append(gap)
    first=cases[0];controls=[]
    for mode in ['primal','sign','claimed_bound','claimed_upper']:
        r=copy.deepcopy(by[first['id']])
        if mode=='primal':r['primal'][0][0]=[999,1]
        elif mode=='sign':r['le_multipliers'][0]=[1,1]
        elif mode=='claimed_bound':r['lower']=[999999,1]
        else:r['upper']=[999999,1]
        try:verify(first,p,r)
        except ValueError as err:controls.append([mode,str(err)])
        else:raise ValueError('false certificate accepted')
    d={'checks':len(by),'rejected':controls,'panels':{}}
    for name,gaps in by_panel.items():
        mean=sum(gaps)/len(gaps);d['panels'][name]=dict(n=len(gaps),zero=sum(g==0 for g in gaps),
            below_0p1=sum(g<F(1,10) for g in gaps),mean_exact=[mean.numerator,mean.denominator],
            mean=float(mean),max=float(max(gaps)),mean_strictly_below_0p1=bool(mean<F(1,10)))
    Path(out).write_text(json.dumps(d,indent=2)+'\n')
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--certificates',type=Path,required=True);a.add_argument('--out',type=Path,required=True)
    x=a.parse_args();run(x.certificates,x.out)
