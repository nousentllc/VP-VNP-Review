"""Cost intervals for the certified AC solutions, computed from exact endpoint arithmetic."""
import gzip,json,re
from fractions import Fraction as F
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def audit(p):
    text=re.sub(r'%[^\n]*','',p.read_text())
    def tab(k):
        return [[F(v) for v in row.split()] for row in re.search(r'mpc\.'+k+r'\s*=\s*\[(.*?)\];',text,re.S)[1].split(';') if row.strip()]
    n=len(tab('bus'));base=F(re.search(r'mpc.baseMVA\s*=\s*([.\d]+)',text)[1])
    active=[(g,c) for g,c in zip(tab('gen'),tab('gencost'),strict=True) if g[7]>0]
    witness=json.loads(gzip.decompress((ROOT/'ac_results'/p.stem/'witnesses.json.gz').read_bytes()))
    vals={}
    for r in witness['starts']:
        if 'proof' not in r:continue
        pr=r['proof'];selected=set(pr['selection']);radius=F(pr['radius'])
        lo=hi=F(0)
        for j,(g,c) in enumerate(active):
            idx=2*n+j
            center=F(r['point'][idx])*base
            a,b=(center-radius*base,center+radius*base) if idx in selected else (center,center)
            if g[8]==g[9]:a=b=g[8]
            A,B,C=c[4:7];candidates=[a,b]
            if A and a<=-B/(2*A)<=b:candidates.append(-B/(2*A))
            ev=[A*z*z+B*z+C for z in candidates];lo+=min(ev);hi+=max(ev)
        assert hi<=F(pr['U']),p
        vals[r['mode']]=[lo,hi]
    gain=None
    if set(vals)=={'dc','flat'}:
        gain=max(vals['dc'][0]-vals['flat'][1], vals['flat'][0]-vals['dc'][1], F(0))
    return dict(case=p.stem,cost_enclosures={k:list(map(str,v)) for k,v in vals.items()},guaranteed_cross_start_improvement=str(gain) if gain is not None else None)
if __name__=='__main__':print(json.dumps([audit(p) for p in sorted((ROOT/'inputs').glob('*.m'))],indent=2))
