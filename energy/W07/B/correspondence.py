"""Audit W07-A and W07-E engineering premises from their released tables.
No optimizer used; A's candidate penalty evaluator is the object under test.
"""
from fractions import Fraction as Q
from functools import lru_cache
from importlib.util import module_from_spec, spec_from_file_location
from itertools import product
from pathlib import Path
import argparse, gzip, hashlib, json, sys

sys.dont_write_bytecode = True
BASE = Path(__file__).resolve().parent.parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def a_check(records):
    spec = spec_from_file_location("penalty_under_test", BASE/"A/model.py")
    production = module_from_spec(spec)
    spec.loader.exec_module(production)
    rows = json.loads(records.read_text())
    shadow = [r for r in rows if r['arm'] == 'shadow']
    design = json.loads((BASE/"A/design.json").read_text())
    assert {r['seed'] for r in shadow} == {s for seeds in design['holdout_by_stratum'].values() for s in seeds}
    assert len(shadow) == len(set(r['seed'] for r in shadow))
    paths = [''.join(bits) for bits in product('01',repeat=5)]
    checks = 0
    cells = 0
    for r in shadow:
        table = r['tables']
        weights = {leaf:Q(v) for leaf,v in r['information']['leaf_weights'].items()}
        assert set(weights) == set(paths) and sum(weights.values()) == 1 and min(weights.values()) > 0
        for t in range(5):
            for h in sorted({p[:t] for p in paths}):
                z = int(h[-1]) if h else 0
                cell = {p:w for p,w in weights.items() if p.startswith(h)}
                p1 = sum(w for p,w in cell.items() if p[t]=='1')/sum(cell.values())
                assert p1 == Q(table[t][z]['q'],8)
                cells += 1
                assert Q(r['information']['issued'][h]['next_q_price_cap'][0]) == p1
                for s,prev in product(range(5),(-1,0,1)):
                    options = production.stage_actions(t,s,prev)
                    for a in options:
                        # E_h[M] for each command AND feasible predecision state, even
                        # when this state would not be visited by the archived incumbent.
                        d0, d1 = (production.delta(table,t,z,s+a,a,k) for k in (0,1))
                        assert (1-p1)*d0+p1*d1 == 0
                        checks += 1
        v={z['tier']:Q(z['value']) for z in r['stages']}
        assert v['PF']<=v['prefix1']<=v['prefix3']<=v['causal']<=Q(r['baseline'])
        assert v['penalty']<=v['causal']
    return dict(families=len(shadow),history_cells=cells,local_state_action_centering_checks=checks,
                leaf_weights_per_family=32,source_sha256=digest(BASE/'A/model.py'),records_sha256=digest(records))


@lru_cache(maxsize=None)
def legal(s,prev,actual,p):
    after=s+actual
    move=11*actual if actual >= 0 else 9*actual
    return (2<=after<=11 and abs(actual)<=p and abs(actual-prev)<=2 and
            (actual>=0 or after>=(2 if p==2 else 5)) and
            all(0<=demand+move<=90 for demand in range(18,49)))


def e_check(kernels):
    with gzip.open(kernels,'rt') as fh:
        data=json.load(fh)
    k, actions = data['values'], data['actions']
    assert len(k)==73 and len(actions)==72
    comparisons=0
    true_actions=0
    strict=0
    for t in range(72,-1,-1):
        assert len(k[t])==5 and all(len(row)==50 for row in k[t])
        for b in range(5):
            for i in range(50):
                s,prev=i//5+2,i%5-2
                if b<4:
                    lo,hi=bool(k[t][b][i]),bool(k[t][b+1][i])
                    assert not hi or lo
                    strict+=int(lo and not hi)
                if t==72:
                    assert bool(k[t][b][i])==(s==9)
                    continue
                pre_powers=[2] if t>=56 else [0,1,2]
                guaranteed=True
                for p in pre_powers:
                    sign=(int(t%24<6)-int(16<=t%24<22)) if p else 0
                    found=False
                    for q in range(-2,3):
                        # E fixes recourse to q+c. The arbitrary future public power
                        # appears at the following state's pre-command quantifier.
                        covers=legal(s,prev,q,p) and -p+int(sign<0)<=q<=p-int(sign>0)
                        for c in ([0,sign] if b and sign else [0]):
                            a=q+c
                            if not covers or not legal(s,prev,a,p):
                                covers=False
                                break
                            j=(s+a-2)*5+a+2
                            if not k[t+1][b-int(c!=0)][j]:
                                covers=False
                                break
                        assert bool(actions[t][p][b][i][q+2])==covers
                        comparisons+=1
                        true_actions+=int(covers)
                        found|=covers
                    guaranteed &= found
                assert bool(k[t][b][i])==guaranteed
    return dict(terminal_states_and_budgets=250,preobservation_occupancy_bits=72*250,
                compared_command_truth_values=comparisons,viable_commands=true_actions,
                strict_adjacent_budget_state_time_cells=strict,
                kernel_sha256=digest(kernels))


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('track',choices=['A','E'])
    parser.add_argument('artifact',type=Path)
    args=parser.parse_args()
    result=(a_check if args.track=='A' else e_check)(args.artifact)
    print(json.dumps(result,sort_keys=True,indent=2))
