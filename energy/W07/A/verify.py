"""Cold read-only independent audit of frozen inputs, public histories, bounds and witnesses."""
from pathlib import Path
from fractions import Fraction as F
from collections import Counter
from itertools import product
import csv, gzip, hashlib, json, sys
import independent as I

def run(base, out):
    lock=json.loads((base/'freeze.json').read_text())
    for name,sha in lock['files'].items():
        assert hashlib.sha256((base/name).read_bytes()).hexdigest()==sha
    design=json.loads((base/'design.json').read_text())
    rows=json.loads((out/'records.json').read_text())
    cases=list(csv.DictReader((out/'families.csv').open()))
    seeds={seed for kind,ss in design['holdout_by_stratum'].items() for seed in ss}
    assert len(cases)==len(seeds)==15 and {int(row['seed']) for row in cases}==seeds
    assert all(row['weight']=='1/15' for row in cases)
    checked=Counter(); tier=Counter()
    for c in cases:
        seed=int(c['seed'])
        arms={row['arm']:row for row in rows if row['seed']==seed}
        assert set(arms)=={'staged','direct','milp','shadow'}
        sh=arms['shadow']; data=sh['tables']
        for key in ('PF','prefix1','prefix3','penalty','causal','analytic'):
            assert I.audit(data,key)==F(c[key])
        cert=json.loads(gzip.decompress((out/f'proof_{seed}.json.gz').read_bytes()))
        for mode in ('causal','center_count'):
            witness={}
            v=I.audit(data,mode,proof=witness)
            assert str(v)==cert[mode]['value'] and witness==cert[mode]['entries']
            checked[mode+'_rows']+=len(witness)
        u=I.audit(data,'policy',sh['baseline_policy']);opt=I.audit(data,'policy',sh['exact_policy'])
        assert u==F(c['baseline']) and opt==F(c['causal']) and u-opt==F(c['gain'])
        assert I.audit(data,'policy',arms['milp']['native']['policy'])==opt
        gate=max(F(15),abs(u)/100); assert gate==F(c['threshold'])
        stages=arms['staged']['stages']; best=None; stopped=False
        for i,entry in enumerate(stages):
            assert entry['tier']==design['stages'][i]
            floor=F(c[entry['tier']]); best=floor if best is None else max(floor,best)
            assert floor==F(entry['value']) and best==F(entry['checked_best'])
            assert not stopped
            stopped=u-best<gate
        assert c['first_stop']==(stages[-1]['tier'] if stopped else 'demonstrated')
        assert stopped==(u-opt<gate)
        assert c['decision']==('excluded' if stopped else 'demonstrated')
        tier[c['first_stop']]+=1
        # Rebuild the issuing-time forecast from transition probabilities, verify rows on identical prefixes.
        info=sh['information']
        mass={leaf:F(1) for leaf in I.BITS}
        seen=set()
        for leaf in reversed(I.BITS):
            for t in range(6):
                h=leaf[:t]; z=int(h[-1]) if h else 0
                observed=data[t][z]; it=info['issued'][h]
                assert it['realized']==observed
                seen.add(h)
                if t==5:
                    assert it['next_q_price_cap'] is None
                else:
                    p=F(observed['q'],8)
                    next_values=[p]+[(1-p)*data[t+1][0][field]+p*data[t+1][1][field] for field in ('price','cap')]
                    assert list(map(F,it['next_q_price_cap']))==next_values
                    mass[leaf]*=p if leaf[t]=='1' else 1-p
        assert set(info['issued'])==seen and mass=={k:F(v) for k,v in info['leaf_weights'].items()}
        assert sum(mass.values())==1 and min(mass.values())>0
        if c['stratum']=='positive':
            plant={h:(1,1,0,0,-1,-1)[len(h)] for h in seen}
            val=I.audit(data,'policy',plant)
            assert val==F(sh['planted_witness_value']) and u-val==F(sh['planted_witness_gain'])
            assert u-val>=gate
            checked['planted_witnesses']+=1
        checked['families']+=1; checked['scenario_leaves']+=len(mass)
    assert I.controls()==json.loads((out/'controls.json').read_text())
    assert len(rows)==len(seeds)*4
    return {'checked':dict(checked),'first_stop':dict(tier),'wrong_target_classifications':0}
if __name__=='__main__':
    base=Path(__file__).resolve().parent
    print(json.dumps(run(base,Path(sys.argv[1]) if len(sys.argv)>1 else base/'results'),indent=2))
