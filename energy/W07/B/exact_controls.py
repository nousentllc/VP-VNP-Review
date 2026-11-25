"""Independent finite enumeration; integer path masses and exact rational money."""
from fractions import Fraction as Q
from itertools import product
import json

PATHS = list(product(range(2), repeat=2))
COMMANDS = list(product(range(2), repeat=4))


def table(masses):
    weights = [Q(n, sum(masses)) for n in masses]
    probability = dict(zip(PATHS, weights))
    costs = []
    for a, b in product(COMMANDS, repeat=2):
        root_common = len(set(a)) == 1
        causal = root_common and b[0] == b[1] and b[2] == b[3]
        overmerged = causal and len(set(b)) == 1
        cost = sum(p*(2*(a[i] != x)+4*(b[i] != z)) for i,((x,z),p) in enumerate(probability.items()))
        penalty = Q(0)
        for i,((x,z),p) in enumerate(probability.items()):
            mean0 = sum(q*2*(a[i] != u) for (u,_),q in probability.items())
            mass_x = sum(q for (u,_),q in probability.items() if u == x)
            mean1 = sum(q*4*(b[i] != v) for (u,v),q in probability.items() if u == x)/mass_x
            penalty += p*(mean0-2*(a[i] != x)+mean1-4*(b[i] != z))
        fitted_bonus = sum(w*4*(x == 1 and b[i] == 1) for i,((x,_),w) in enumerate(probability.items()))
        costs.append((cost, penalty, fitted_bonus, root_common, causal, overmerged, a, b))
    return costs


def study(masses):
    rows = table(masses)
    causal = [r for r in rows if r[4]]
    data = dict(pf=min(r[0] for r in rows), partial=min(r[0] for r in rows if r[3]),
                causal=min(r[0] for r in causal), false_merge=min(r[0] for r in rows if r[5]),
                centered_floor=min(r[0]+r[1] for r in rows),
                fitted_floor=min(sum(r[:3]) for r in rows),
                maximum_bias=max(r[1]+r[2] for r in causal))
    assert all(r[1] == 0 for r in causal)
    assert data['pf'] <= data['partial'] <= data['causal']
    assert data['centered_floor'] == data['causal']
    assert data['fitted_floor']-data['maximum_bias'] <= data['causal']
    base = next(r for r in rows if all(v == 0 for v in r[6]+r[7]))
    assert base[1]+base[2] == 0
    data.update(arrays=len(rows),causal_arrays=len(causal),baseline=base[0],fitted_mean=base[1]+base[2])
    return data


def viability_controls():
    # No charging during the obligation. The policy chooses a reserve offer before the
    # adversary calls. A firm 1-block downward call uses one unit of energy.
    # A second implementation expands every possible call word at that budget.
    horizon = 4
    sets = [set(range(5)) for _ in range(5)]
    for _ in range(horizon):
        sets = [{x for x in range(5) if x in sets[b] and
                 (b == 0 or x-1 in sets[b-1])} for b in range(5)]
    direct = [{x for x in range(5) if all(x >= sum(seq) for seq in product(range(2),repeat=horizon)
                                          if sum(seq) <= b)} for b in range(5)]
    assert sets == direct and all(sets[b+1] <= sets[b] for b in range(4))
    assert 1 in sets[1] and 1 not in sets[2]
    return [sorted(s) for s in sets]


def main():
    nominal = study([3,1,1,3])
    assert [nominal[k] for k in ('pf','partial','causal','false_merge','centered_floor','fitted_floor','maximum_bias')] == [0,1,2,3,2,3,2]
    panels = [study(p) for p in product((1,2),repeat=4)]
    omitted = Q(9,10)*0 + Q(1,10)*100
    observed_fixed = [sum(Q(1,2)*(1 if x == a else -1) for x in range(2)) for a in range(2)]
    adapt_mean = sum(Q(1,2)*1 for x in range(2))
    assert observed_fixed == [0,0] and adapt_mean == 1
    assert omitted == 10 and 1 <= nominal['baseline']-nominal['causal']
    result=dict(branching=nominal,mass_sensitivity=dict(positive_weight_panels=len(panels),
                tested_arrays=sum(p['arrays'] for p in panels),centered_reproduced=sum(
                p['centered_floor']==p['causal'] for p in panels)),
                omitted_original_weight_gain=omitted,renormalized_retained_gain=0,
                marginal_means=observed_fixed,history_chosen_mean=adapt_mean,
                missing_baseline_examples=dict(same_floor=0,possible_costs=[0,12],selected_target=1),
                strict_threshold=dict(target=1,equality_achieved=True),
                no_recharge_budget_kernels=viability_controls())
    print(json.dumps(result,default=str,sort_keys=True,indent=2))


if __name__ == '__main__':
    main()
