"""Audit outer-cut orientations with rational rank-one test points and independent tapped branch flow."""
from review import ROOT,OUT,F,json,read,math,cmath,re
from collections import Counter
from pathlib import Path


def mul(w,z):
    a,b=w;c,d=z
    return a*c-b*d,a*d+b*c


def conj(z):return z[0],-z[1]


def audit(imaginary_sign):
    counts=Counter(); smallest=1.
    for p in sorted((ROOT/'inputs').glob('*.m')):
        text=re.sub("%[^\n]*","",p.read_text())
        def parse(n):
            return [list(map(F,s.split())) for s in re.search('mpc\\.'+n+r'\s*=\s*\[([^\]]*)\]',text)[1].split(';') if s.strip()]
        buses=parse('bus');branches=[b for b in parse('branch') if b[10]>0]; M=float(re.search(r'mpc.baseMVA\s*=\s*([.\d]+)',text)[1]);n=len(buses); ids={b[0]:k for k,b in enumerate(buses)}
        path=ROOT/'ac_results'/p.stem; record=read(path/'witnesses.json.gz')
        # Tapped physical midpoint is independently computed in review.py. Here reconstruct
        # both ends from the canonical sorted lifted pair with each row's stored orientation.
        for s in record['starts']:
            V=[complex(a,b) for a,b in zip(s['point'][:n],s['point'][n:2*n])]
            for b in branches:
                i,j=ids[b[0]],ids[b[1]]; y=1/complex(float(b[2]),float(b[3])); t=(float(b[8]) or 1)*cmath.exp(1j*math.radians(float(b[9])))
                ch=.5j*float(b[4]);iF=(V[i]/t-V[j])*y+(V[i]/t)*ch;iT=(V[j]-V[i]/t)*y+V[j]*ch
                true=[V[i]/t*iF.conjugate(),V[j]*iT.conjugate()]
                pair=V[min(i,j)]*V[max(i,j)].conjugate()
                for side,(u,v,aa,ab) in enumerate([(i,j,(y+ch)/abs(t)**2,-y/t.conjugate()),(j,i,y+ch,-y/t)]):
                    sign=1 if u<v else -1
                    real=aa.real*abs(V[u])**2+ab.real*pair.real+sign*ab.imag*pair.imag
                    imag=-aa.imag*abs(V[u])**2-ab.imag*pair.real+sign*ab.real*pair.imag
                    assert abs(complex(real,imag)-true[side])*M < 1e-7
                    counts['oriented_branch_ends']+=1
        # Arbitrary exact rational voltage vectors (may be physically infeasible).
        V=[(F((j+2)%7-3,4),F((3*j+1)%11-5,5)) for j in range(n)]
        for kind,obj,*args in record['cuts']:
            if kind!='soc':continue
            i,j=obj;z=list(map(F,args)); wi=sum(a*a for a in V[i]);wj=sum(a*a for a in V[j])
            ab=mul(V[i],conj(V[j]));lhs=wi+wj*sum(a*a for a in z)-2*(z[0]*ab[0]+z[1]*ab[1])
            zz=mul(z,V[j]);rhs=sum((a-b)**2 for a,b in zip(V[i],zz))
            assert lhs==rhs and lhs>=0
            counts['soc_rank_one_identities']+=1
        clique=ROOT/'exploratory/results'/p.stem/'proof.json.gz'
        if not clique.exists():continue
        for round in read(clique):
            for cl,Z in round['psd']:
                z=[tuple(map(F,v)) for v in Z];lhs=F(0);total=(0,0)
                for k,(i,zi) in enumerate(zip(cl,z)):
                    v=mul(conj(zi),V[i]); total=(total[0]+v[0],total[1]+v[1])
                    lhs+=sum(b*b for b in zi)*sum(b*b for b in V[i])
                    for j,zj in zip(cl[k+1:],z[k+1:]):
                        x,y=mul(V[i],conj(V[j])); a,b=zi;c,d=zj
                        lhs+=2*(a*c+b*d)*x+imaginary_sign*2*(a*d-b*c)*y
                assert lhs==sum(v*v for v in total) and lhs>=0
                counts['clique_rank_one_identities']+=1
    return counts


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--source',type=Path,default=ROOT)
    parser.add_argument('--out',type=Path,required=True)
    opt=parser.parse_args();ROOT=opt.source.resolve();OUT=opt.out
    OUT.mkdir(parents=True,exist_ok=True)
    counts=audit(-1);rejected=False
    try:audit(1)
    except AssertionError:rejected=True
    assert rejected
    (OUT/'ac_lifts.json').write_text(json.dumps(dict(checks=counts,wrong_psd_imag_sign_rejected=rejected),indent=2)+'\n')
    print(counts)
