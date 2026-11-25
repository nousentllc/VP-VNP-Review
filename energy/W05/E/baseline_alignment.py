"""Compare stored live fill shedding and end stock with the exact hindsight certificate."""
import argparse,gzip,json
from fractions import Fraction as F
from pathlib import Path
from verify_bounds import verify
ROOT=Path(__file__).resolve().parent

def run(raw,certs,out):
    pack=json.loads(gzip.decompress((ROOT/'inputs/holdout.json.gz').read_bytes()))
    cases={c['id']:c for c in pack['cases']}
    witnesses={c['case']:c for c in json.loads(gzip.decompress(Path(certs).read_bytes()))}
    by={}
    with gzip.open(raw,'rt') as f:
        for line in f:
            r=json.loads(line)
            if r['arm']!='rule12':continue
            c=cases[r['case']];w=witnesses[r['case']];panel=c['panel'];a=r['actions']
            if any(d['reason'] is not None for d in r['decisions']):raise ValueError('observed fill used fallback')
            observed=sum(F(float(h[3])) for h in a)
            nominal=F(*w['upper']);lower=F(*w['lower']);end=F(*w['primal'][-1][-1])
            if end<F(float(c['floor'][-1])) or end>F(float(pack['parameters']['energy'])):raise ValueError('terminal')
            _,weights=verify(c,pack['parameters'],w,with_weights=True)
            z=by.setdefault(panel,[]);z.append((observed-lower,abs(observed-nominal),
                   abs(F(float(a[-1][-1]))-end),end,float(sum(h[3] for h in a))-float(observed),weights))
    summary={}
    for panel,z in by.items():
        n=len(z);gap=sum(x[0] for x in z)/n;terms=[t[3] for t in z]
        robust=gap+F(1,100000)*sum(t[5] for t in z)/n
        summary[panel]=dict(days=n,uniform_row_box_relaxation=1e-5,relaxed_possible_gain=float(robust),
            relaxed_strict_below_point_one=robust<F(1,10),exact_stored_float_sum_minus_lower_mean=[gap.numerator,gap.denominator],
            stored_mean_possible_gain=float(gap),max_shed_cost_difference=float(max(x[1] for x in z)),
            max_terminal_abs_error=float(max(x[2] for x in z)),terminal_min=float(min(terms)),
            terminal_mean=float(sum(terms)/n),terminal_max=float(max(terms)),
            max_float_accumulation_roundoff=max(abs(x[4]) for x in z),strict_below_point_one=gap<F(1,10))
    Path(out).write_text(json.dumps(summary,indent=2)+'\n')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--raw',type=Path,required=True);p.add_argument('--certificates',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True);a=p.parse_args();run(a.raw,a.certificates,a.out)
