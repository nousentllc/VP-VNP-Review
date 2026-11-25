"""Independent engineering checks on continuous AC nominal points and exact chronological UC witnesses."""
from pathlib import Path
import cmath,math,json,re
from fractions import Fraction as F
from linear import Linear,read,write
from commitment import build
HERE=Path(__file__).resolve().parent


def nominal(path,pt):
    s=re.sub(r'%[^\n]*','',path.read_text())
    def matrix(key):
        return [[float(v) for v in r.split()] for r in re.search(r'mpc\.'+key+r'\s*=\s*\[(.*?)\];',s,re.S)[1].split(';') if r.strip()]
    b=float(re.search(r'mpc.baseMVA\s*=\s*([.\d]+)',s)[1]);bus=matrix('bus')
    gen=[v for v in matrix('gen') if v[7]>0];n=len(bus);indices={r[0]:i for i,r in enumerate(bus)}
    V=[complex(pt[i],pt[n+i]) for i in range(n)]
    inj=[complex(r[2],r[3])+complex(r[4],-r[5])*abs(v)**2 for r,v in zip(bus,V)]
    ex=[]
    for r in matrix('branch'):
        if r[10]<=0:continue
        i,j=indices[r[0]],indices[r[1]]
        tap=(r[8] or 1)*cmath.exp(1j*math.radians(r[9]));a=V[i]/tap;c=V[j];series=(a-c)/complex(r[2],r[3])
        sf=b*a*(series+1j*r[4]*a/2).conjugate();st=b*c*(-series+1j*r[4]*c/2).conjugate()
        inj[i]+=sf;inj[j]+=st
        if r[5]>0:ex.extend([abs(sf)-r[5],abs(st)-r[5]])
        angle=math.degrees(cmath.phase(V[i])-cmath.phase(V[j]));ex.extend([r[11]-angle,angle-r[12]])
    for k,r in enumerate(gen):
        pg=pt[2*n+k]*b;qg=pt[2*n+len(gen)+k]*b
        inj[indices[r[0]]]-=complex(pg,qg);ex.extend((r[9]-pg,pg-r[8],r[4]-qg,qg-r[3]))
    for i,r in enumerate(bus):ex.extend((r[12]-abs(V[i]),abs(V[i])-r[11]))
    return max(abs(v) for v in inj),max(0.,*ex)


def uc(path,periods,rec):
    d=json.loads(path.read_text(),parse_float=F);lp=build(path,periods)
    x=dict(zip(lp.names,map(F,read(rec/'certificate.json.gz')['primal']),strict=True))
    def at(field,*indices):return x[field+'['+','.join(map(str,indices))+']']
    supply=[F(0)]*periods;reserve=supply.copy();cost=F(0)
    for name,g in d['thermal_generators'].items():
        before=g['unit_on_t0'];age=g['time_up_t0'] if before else g['time_down_t0']
        prior_p=before*(g['power_output_t0']-g['power_output_minimum'])
        for t in range(1,periods+1):
            u,v,w,p,r,c=[at(key,name,t) for key in ('ug','vg','wg','pg','rg','cg')]
            assert u in (0,1) and v==max(0,u-before) and w==max(0,before-u)
            if u!=before:
                assert age>=(g['time_up_minimum'] if before else g['time_down_minimum']);age=0
            age+=1
            assert r>=0 and p>=0 and u>=g['must_run']
            assert p+r<=u*(g['power_output_maximum']-g['power_output_minimum'])
            assert p+r-prior_p<=g['ramp_up_limit'] and prior_p-p<=g['ramp_down_limit']
            if v:assert p+r+g['power_output_minimum']<=g['ramp_startup_limit']
            if w:assert prior_p+g['power_output_minimum']<=g['ramp_shutdown_limit']
            pts=g['piecewise_production'];weights=[at('lg',name,k,t) for k in range(len(pts))]
            assert min(weights)>=0 and sum(weights)==u
            assert sum(a*(b['mw']-pts[0]['mw']) for a,b in zip(weights,pts))==p
            fuel=sum(a*b['cost'] for a,b in zip(weights,pts));assert fuel==c+u*pts[0]['cost']
            starts=[at('dg',name,k,t) for k in range(len(g['startup']))];assert sum(starts)==v
            cost+=fuel+sum(a*b['cost'] for a,b in zip(starts,g['startup']))
            supply[t-1]+=p+u*g['power_output_minimum'];reserve[t-1]+=r;before=u;prior_p=p
    for name,g in d['renewable_generators'].items():
        for i in range(periods):
            p=at('pw',name,i+1);assert g['power_output_minimum'][i]<=p<=g['power_output_maximum'][i];supply[i]+=p
    assert supply==d['demand'][:periods] and all(a>=b for a,b in zip(reserve,d['reserves']))
    assert cost==F(read(rec/'summary.json')['U'])
    return dict(thermal=len(d['thermal_generators']),periods=periods,exact_cost=str(cost))


def controls():
    # min 2x-y, x+y>=1, x in [0,2], y in [-1,1]. True optimum -1 at (0,1).
    a=Linear();a.var('x',0,2,2);a.var('y',-1,1,-1);a.row('lower',{0:1,1:1},1,None)
    U=a.feasible([F(0),F(1)])
    for y in map(F,[0,1,2,7]):assert a.dual([y])<=U
    try:a.dual([F(-1)])
    except ValueError:pass
    else:raise AssertionError('Invalid row sign accepted')
    # Wrong upper endpoint for a positive reduced cost makes a spurious bound.
    assert 2*2-1>U
    return 'four valid duals, wrong-sign rejection and false-stop endpoint counterexample'


if __name__=='__main__':
    import sys
    acdir,ucdir,out=map(Path,sys.argv[1:4]);result=dict(controls=controls(),ac={},uc={})
    for p in (HERE/'inputs').glob('*.m'):
        trials=read(acdir/p.stem/'witnesses.json.gz')['starts']
        check=[nominal(p,r['point']) for r in trials if 'proof' in r]
        assert all(m<1e-5 and v<1e-6 for m,v in check)
        result['ac'][p.name]=check
    for p in (HERE/'inputs').glob('20*.json'):
        for T in (24,48):result['uc'][f'{p.stem}_{T}']=uc(p,T,ucdir/f'{p.stem}_{T}')
    write(out,result)
