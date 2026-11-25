"""Independently reconstruct tapped terminal flows by polarization and check outward LP row widths."""
import json,re
from fractions import Fraction as F
from pathlib import Path
from flint import arb,acb,ctx,fmpq
from network import Grid
from ac_bound import Outer
D=Path(__file__).resolve().parent

def interval(x):
    q=F(x)
    return arb(fmpq(q.numerator,q.denominator))
def coefficients(br,base,reverse_phase=False):
    # Device equations in coordinates on the series side of the ideal transformer.
    y=1/acb(interval(br[2]),interval(br[3]))
    angle=interval(br[9])*arb.pi()/180
    if reverse_phase:angle=-angle
    tap=interval(br[8] or 1)*acb(angle.cos(),angle.sin())
    ch=acb(0,interval(br[4]/2))
    def flows(a,b):
        v=a/tap
        through=(v-b)*y
        return [base*v*(through+ch*v).conjugate(),base*b*(-through+ch*b).conjugate()]
    f10,f01,f11,fi1=[flows(acb(a),acb(b)) for a,b in [(1,0),(0,1),(1,1),(1j,1)]]
    return [[f10[s],f01[s],f11[s]-f10[s]-f01[s],fi1[s]-f10[s]-f01[s]] for s in (0,1)]

def audit(p):
    # Freeze the production hull at its declared precision before testing with independent 240-bit intervals.
    ctx.prec=160;grid=Grid(p);h=Outer(grid);ctx.prec=240
    txt=re.sub(r'%[^\n]*','',p.read_text())
    def table(k):
        return [[F(v) for v in row.split()] for row in re.search(r'mpc\.'+k+r'\s*=\s*\[(.*?)\];',txt,re.S)[1].split(';') if row.strip()]
    bus=table('bus');brs=[x for x in table('branch') if x[10]];idx={b[0]:n for n,b in enumerate(bus)}
    rows={n:(c,lo,hi) for n,c,lo,hi in h.lp.rows}
    base=interval(F(re.search(r'mpc.baseMVA\s*=\s*([.\d]+)',txt)[1]));checks=0;zero_width=0
    for k,br in enumerate(brs):
        i,j=idx[br[0]],idx[br[1]]
        a,b=sorted((i,j));zr,zi=h.pairs[a,b]
        for side,coeff in enumerate(coefficients(br,base)):
            for part in range(2):
                col=h.flow[2*k+side][part];co,low,high=rows['flow'+str(col)]
                assert co[col]==1 and -low==high and high>=0
                ax=[(h.w[i],coeff[0]),(h.w[j],coeff[1]),(zr,coeff[2]),(zi,coeff[3] if i<j else -coeff[3])]
                assert set(co)<=set([col]+[u for u,_ in ax])
                delta=interval(0)
                for u,cx in ax:
                    actual=cx.imag if part else cx.real
                    delta+=abs(actual+interval(co.get(u,0)))*interval(max(abs(v) for v in h.lp.box[u]))
                if high==0:
                    # Interval cancellation in polarization can leave an O(2^-precision) radius.
                    # Use the exact rational rectangular formula for the unshifted case.
                    assert br[9]==0
                    yre=br[2]/(br[2]**2+br[3]**2);yim=-br[3]/(br[2]**2+br[3]**2)
                    tap=br[8] or F(1); scale=F(re.search(r'mpc.baseMVA\s*=\s*([.\d]+)',txt)[1])
                    dg=(yre,-(yim+br[4]/2)); cr=(-yre/tap,yim/tap)
                    for axis,(u,_) in enumerate(ax):
                        if axis in (0,1):
                            exact=dg[part]/(tap**2 if side==0 else 1) if axis==side else 0
                        elif axis==2:exact=cr[part]
                        else:exact=(-cr[1] if part==0 else cr[0])*(1 if i<j else -1)*(1 if side==0 else -1)
                        assert co.get(u,0)==-scale*exact
                    zero_width+=1
                else:assert delta<=interval(high),(p.name,k,side,part,str(delta),str(high))
                checks+=1
    return dict(case=p.name,physical_branches=len(brs),both_end_rows=checks,exact_zero_width=zero_width,
                nonunity_taps=sum(q[8] not in (0,1) for q in brs),nonzero_phase_shifts=sum(q[9]!=0 for q in brs))
def main():
    result=[audit(p) for p in sorted((D/'inputs').glob('*.m'))]
    # Synthetic directed transformer exercises a sign not necessarily present in a fresh case.
    br=list(map(F,['1','2','.017','.18','.026','100','100','100','1.08','17','1','-30','30']))
    c=coefficients(br,interval(100));bad=coefficients(br,interval(100),True)
    assert not c[0][2].overlaps(bad[0][2]) and not c[1][2].overlaps(bad[1][2])
    assert not c[0][0].overlaps(c[1][0])
    print(json.dumps(dict(cases=result,synthetic_phase_reversal_detected_at_both_ends=True,precision_bits=240),indent=2))
if __name__=='__main__':main()
