"""Independent MATPOWER parse, full start and score review, and terminal/deadline controls."""
import argparse
import hashlib
import itertools
import json
import re
from pathlib import Path
import numpy as np
from scipy import sparse
from scipy.sparse.linalg import spsolve

HERE=Path(__file__).resolve().parent
ARMS=['full_dc','full_matched','all','degree','guided']

def parse(path):
    txt='\n'.join(line.partition('%')[0] for line in path.read_text().splitlines())
    def field(k):
        body=re.search(r'\bmpc\.'+k+r'\s*=\s*\[([^\]]*)\]',txt,re.S)[1]
        return np.array([[float(v) for v in r.split()] for r in body.split(';') if r.strip()])
    base=float(re.search(r'\bmpc\.baseMVA\s*=\s*([^;]+);',txt)[1])
    bus,g,br,c=map(field,['bus','gen','branch','gencost']);assert len(c)==len(g)
    keep=g[:,7]>0;g,c=g[keep],c[keep]
    assert np.all(c[:,0]==2) and np.all(c[:,3]==3)
    assert br.shape[1]>=13 and g.shape[1]>=10
    br=br[br[:,10]>0]
    idx={int(r[0]):i for i,r in enumerate(bus)};assert len(idx)==len(bus)
    gb,fr,to=(np.array([idx[int(v)] for v in vv]) for vv in [g[:,0],br[:,0],br[:,1]])
    assert not np.any(fr==to)
    ref=np.flatnonzero(bus[:,1]==3);assert len(ref)==1
    return base,bus,g,br,c[:,4:7],gb,fr,to,int(ref[0])
def power(net,v,theta):
    base,bus,g,br,c,gb,fr,to,ref=net
    voltage=v*np.exp(1j*theta)
    demand=(bus[:,2]+1j*bus[:,3])+(bus[:,4]-1j*bus[:,5])*v**2
    ff=[];tt=[]
    for row,i,j in zip(br,fr,to):
        tp=(row[8] or 1.)*np.exp(1j*np.deg2rad(row[9]))
        v_internal=voltage[i]/tp
        series=(v_internal-voltage[j])/complex(row[2],row[3])
        cur_from=(series+v_internal*.5j*row[4])/np.conjugate(tp)
        cur_to=-series+voltage[j]*.5j*row[4]
        s_from=base*voltage[i]*np.conjugate(cur_from);s_to=base*voltage[j]*np.conjugate(cur_to)
        demand[i]+=s_from;demand[j]+=s_to;ff.append(s_from);tt.append(s_to)
    return demand,np.array(ff),np.array(tt)
def reconstructed(net):
    base,bus,g,br,c,gb,fr,to,ref=net;n=len(bus);m=len(br)
    p=g[:,9].copy();q=np.clip(np.zeros(len(g)),g[:,4],g[:,3]);left=sum(bus[:,2])-sum(p)
    # Frozen generator-order tie convention; independently build the DC bus admittance sparse.
    for j in np.argsort(c[:,1]+c[:,0]*(g[:,8]+g[:,9])):
        delta=np.clip(left,0,g[j,8]-p[j]);p[j]+=delta;left-=delta
    rows=np.tile(np.arange(m),2)
    inc=sparse.csr_matrix((np.r_[np.ones(m),-np.ones(m)],(rows,np.r_[fr,to])),shape=(m,n))
    w=1/(br[:,3]*np.where(br[:,8]!=0,br[:,8],1))
    L=(inc.T@sparse.diags(w)@inc).tocsc()
    injection=(-bus[:,2]+np.bincount(gb,p,minlength=n))/base
    rhs=injection+inc.T@(w*np.deg2rad(br[:,9]))
    skip=np.arange(n)!=ref;theta=np.zeros(n);theta[skip]=spsolve(L[skip][:,skip],rhs[skip])
    v=np.ones(n).clip(bus[:,12],bus[:,11]);req=power(net,v,theta)[0]
    pcommon,qcommon=p.copy(),q.copy()
    for i in np.unique(gb):
        loc=np.flatnonzero(gb==i)
        for z,delta,cap in [(pcommon,req[i].real-p[loc].sum(),g[loc,8]-g[loc,9]),
                            (qcommon,req[i].imag-q[loc].sum(),g[loc,3]-g[loc,4])]:
            fractions=cap/cap.sum() if cap.sum()>0 else np.full(len(loc),1./len(loc))
            z[loc]+=fractions*delta
    return (v,theta,p,q),(v,theta,pcommon,qcommon)
def choose(net,arm):
    _,bus,g,br,c,gb,fr,to,_=net
    neighbors=[[] for _ in bus]
    for i,j in zip(fr,to):neighbors[i].append(int(j));neighbors[j].append(int(i))
    sets=list(map(set,neighbors));piv={};scores={}
    for i in set(gb):
        ids=np.flatnonzero(gb==i).tolist()
        widths=g[:,8]-g[:,9]+g[:,3]-g[:,4]
        policy=sorted(ids,key=lambda j:(-widths[j],j))
        if arm=='guided':
            policy=sorted(ids,key=lambda j:(bool(c[j,0]!=0),-widths[j],j))
            off=sum(int(x not in sets[y]) for x,y in itertools.combinations(sets[i],2))
            k=2+2*len(sets[i])+len(ids)-1
            scores[int(i)]=off+int(c[policy[0],0]!=0)*(k*(k-1)//2)
        if arm=='all' or arm=='degree' and len(neighbors[i])<=3 or arm=='guided' and scores[int(i)]<=6:
            piv[int(i)]=policy[0]
    return piv,scores

def audit_point(net,point,tol):
    base,bus,g,br,c,gb,fr,to,ref=net;v,theta,p,q=point
    dem,sfrom,sto=power(net,v,theta)
    gen=np.bincount(gb,p,minlength=len(v))+1j*np.bincount(gb,q,minlength=len(v))
    res=gen-dem;rate=br[:,5]>0
    def box(x,lo,hi):return max(0.,float(max(np.max(lo-x),np.max(x-hi))))
    thermal=max(0.,float(np.max(np.maximum(abs(sfrom[rate]),abs(sto[rate]))-br[rate,5]))) if rate.any() else 0.
    defects={'gen':max(box(p,g[:,9],g[:,8]),box(q,g[:,4],g[:,3])),
             'balance':float(max(np.max(abs(res.real)),np.max(abs(res.imag)))),'thermal':thermal,
             'vm':box(v,bus[:,12],bus[:,11]),'delta':box(np.rad2deg(theta[fr]-theta[to]),br[:,11],br[:,12]),
             'theta':max(0.,float(np.max(abs(theta))-2*np.pi)),'ref':abs(theta[ref])}
    valid=all(np.isfinite(z).all() for z in point) and max(defects[k] for k in ('gen','balance','thermal'))<=tol['physics_tol_MVA'] and defects['vm']<=1e-7 and defects['delta']<=tol['angle_tol_deg'] and defects['theta']<=1e-7 and defects['ref']<1e-7
    cost=float(c[:,0]@(p*p)+c[:,1]@p+c[:,2].sum())
    return defects,bool(valid),cost

def run(raw):
    lock=json.loads((HERE/'freeze.json').read_text());tol=json.loads((HERE.parents[1]/'W04/foundation/protocol/design.json').read_text())['C']
    allcases=[];counts=dict(records=0,terminal_vectors=0,valid=0,valid_by_12s=0,late_valid=0,corruptions_rejected_from_valid=0,rep0=0)
    for file in sorted((HERE/'inputs').glob('*.m')):
        sha=hashlib.sha256(file.read_bytes()).hexdigest()
        assert lock['hashes']['W05/C/inputs/'+file.name]==sha
        net=parse(file);base,bus,g,br,c,gb,fr,to,ref=net
        dc,common=reconstructed(net);local=[]
        mV=mTheta=mP=mQ=mbox=mcost=mcross=0.;stored={}
        for arm in ARMS:
            piv,scores=choose(net,arm)
            q=dict(arm=arm,expected_pivots=len(piv),selected_quadratic=sum(bool(c[j,0]) for j in piv.values()),
                   total_guided_candidates=len(scores),by_12s=0)
            local.append(q)
            for rep in range(lock['repeats']):
                f=raw/(file.stem+'_'+arm+'_'+str(rep)+'.json')
                if not f.exists():q.setdefault('missing',[]).append(rep);continue
                rr=json.loads(f.read_text());counts['records']+=1
                if 'error' in rr:q.setdefault('errors',[]).append(rep);continue
                assert rr['repeat']==rep and rr['case']==file.stem and rr['policy']==arm
                assert {int(k):j for k,j in rr['pivots'].items()}==piv
                assert {int(k):j for k,j in rr['scores'].items()}==scores
                assert rr['n_variables']==2*len(bus)+2*(len(g)-len(piv))
                u=[np.array(p) for p in rr['variables']]
                residual,ok,cost=audit_point(net,u,tol);assert ok==rr['check']['valid']
                assert rr['within_deadline']==(rr['elapsed']<=12)
                counts['terminal_vectors']+=1
                if ok:
                    counts['valid']+=1
                    if rr['elapsed']<=12:counts['valid_by_12s']+=1;q['by_12s']+=1
                    else:counts['late_valid']+=1
                    pert=[x.copy() for x in u];pert[2][0]+=1
                    assert not audit_point(net,pert,tol)[1] and rr['corrupt_rejected']
                    counts['corruptions_rejected_from_valid']+=1
                mcost=max(mcost,abs(cost-rr['check']['cost']))
                if rep==0:
                    counts['rep0']+=1
                    v=tuple(np.array(z) for z in rr['initial_vectors']);stored[arm]=v
                    target=dc if arm=='full_dc' else common
                    e=[float(np.max(abs(x-y))) for x,y in zip(v,target)]
                    mV=max(mV,e[0]);mTheta=max(mTheta,e[1]);mP=max(mP,e[2]);mQ=max(mQ,e[3])
                    ff=audit_point(net,v,tol)[0]
                    mbox=max(mbox,abs(ff['gen']-rr['reconstructed_start_box_MW_MVAr']))
                    q['initial_generator_box_violation']=ff['gen']
        if 'full_matched' in stored:
            for arm in ['all','degree','guided']:
                if arm in stored:
                    delta=[float(np.max(abs(x-y))) for x,y in zip(stored[arm],stored['full_matched'])]
                    mcross=max(mcross,*delta)
        assert max(mV,mTheta,mP,mQ,mcross,mbox)<=1e-6 and mcost<=1e-5
        allcases.append(dict(case=file.stem,sha256=sha,buses=len(bus),online_generators=len(g),nonzero_quadratic_costs=int(np.sum(c[:,0]!=0)),
            colocated_buses=int(sum(np.bincount(gb)>1)),max_saved_matched_start_difference=mcross,
            max_independent_initial_difference=dict(voltage_pu=mV,theta_rad=mTheta,P_MW=mP,Q_MVAr=mQ),
            max_initial_box_disagreement=mbox,max_cost_difference=mcost,policy=local))
    return dict(cases=allcases,counts=counts,scope='Common physical tuple before IPOPT initialization. Voltage, angles and P,Q comparisons retain their native units. A complete primary panel has 125 records and 25 initial vectors.')
if __name__=='__main__':
    cli=argparse.ArgumentParser();cli.add_argument('--raw',type=Path,required=True);cli.add_argument('--out',type=Path,required=True)
    a=cli.parse_args();out=run(a.raw);a.out.write_text(json.dumps(out,indent=2)+'\n')
