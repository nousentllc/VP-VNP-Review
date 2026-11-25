"""Independent, deterministic exact audits for W04-B. Uses Python's standard library."""
from fractions import Fraction as Q
from itertools import product
import json


def check_contracts():
    levels = (Q(-1, 2), Q(0), Q(3, 2))
    costs = list(product(levels, repeat=2))
    maps = list(product((0, 1), repeat=2))
    counts = dict(map_pairs=0, candidates=0, exact_map_pairs=0, tight=0)
    for full, reduced, project, lift in product(costs, costs, maps, maps):
        alpha = max(Q(0), *(reduced[project[i]] - full[i] for i in (0, 1)))
        beta = max(Q(0), *(full[lift[j]] - reduced[j] for j in (0, 1)))
        assert min(reduced)-alpha <= min(full) <= min(reduced)+beta
        counts['map_pairs'] += 1
        if alpha == beta == 0:
            for t in sorted(set(full + reduced)):
                assert any(x <= t for x in full) == any(y <= t for y in reduced)
            counts['exact_map_pairs'] += 1
        for j in (0, 1):
            epsilon = reduced[j]-min(reduced)
            regret = full[lift[j]]-min(full)
            assert 0 <= regret <= alpha+beta+epsilon
            candidate_beta = full[lift[j]]-reduced[j]
            assert regret <= alpha+candidate_beta+epsilon
            counts['candidates'] += 1
            counts['tight'] += regret == alpha+beta+epsilon
    return counts


def check_witnesses():
    costs = (1, 0)
    assert min(costs) == 0 < min([costs[0]])
    assert min([0]) == min([0, 0]) and True not in [False]
    swapped_cost = abs(1-0)+abs(0-1)
    assert swapped_cost == 2 and abs((1+0)-(0+1)) == 0
    target = (0, 0)
    discharge = lambda start: all(abs(b-a) <= 1 for a,b in zip(start,target))
    assert sum((2, 0)) == sum((1, 1)) and not discharge((2, 0)) and discharge((1, 1))
    assert min(costs[:1]) == 1 > min(costs)
    deltas = [Q(1, 2)*(rho-Q(4,5))/eta for rho,eta in [(Q(4,5),1),(Q(81,100),Q(9,10))]]
    assert deltas == [0, Q(1,180)]
    # Two hours, disjoint charging and discharging, C=2, P=1, initial SOC=1 per device.
    paths = []
    for eta_c,eta_d in [(Q(4,5),Q(1)),(Q(9,10),Q(9,10))]:
        soc = Q(1)
        path = [soc]
        for charge,discharge_power in [(Q(1,2),Q(0)),(Q(0),Q(2,5))]:
            assert 0 <= charge <= 1 and 0 <= discharge_power <= 1 and charge*discharge_power==0
            soc += eta_c*charge - discharge_power/eta_d
            assert 0 <= soc <= 2
            path.append(soc)
        paths.append(path)
    assert [p[-1]-p[0] for p in paths]==deltas
    assert abs(3-2)<=1<abs(3-0)
    assert min(x for x in (0,1) if x>=Q(1,2)) == 1 > Q(1,2)
    assert 0 in {0} and 1 in {0,1} and (min(0,1),1)==(0,1)
    return {'missing_lift':[0,1], 'orphan_optimizer':True,'labeled_costs':[swapped_cost,0],
            'unbalanced_discharge':[False,True], 'invalid_global_lower_bound':[1,0],
            'nonzero_cycle_terminal_residuals':list(map(str,deltas)), 'tolerance_soc_paths':[list(map(str,p)) for p in paths], 'history_ramp':[True,False],
            'integer_and_lp_minima':['1','1/2'], 'retained_and_overwritten_costs':[0,1]}


def check_labeled_lift():
    """Test the literal Lean label convention and its fixed permutation in the W03 Python replay."""
    states = transitions = 0
    for n in range(1,8):
        for cap in range(1,7):
            coordinates = {}
            for total in range(n*cap+1):
                quotient,remainder = divmod(total,n)
                devices = tuple(quotient + (i < remainder) for i in range(n))
                previous = tuple((total+i)//n for i in range(n))
                assert devices == previous[::-1]
                assert sum(devices) == total and all(0<=x<=cap for x in devices)
                coordinates[total] = devices
                states += 1
            for total,devices in coordinates.items():
                for rate in range(4):
                    for endpoint in range(max(0,total-n*rate),min(n*cap,total+n*rate)+1):
                        step = [b-a for a,b in zip(devices,coordinates[endpoint])]
                        assert all(abs(d)<=rate for d in step) and sum(map(abs,step))==abs(endpoint-total)
                        transitions += 1
    return dict(states=states, rate_conditioned_transitions=transitions,
                label_relation='W03 Python coordinate i equals Lean coordinate N-1-i')


def check_sharpness():
    n = 0
    for a,b,e in product((Q(0),Q(1,3),Q(5,2)), repeat=3):
        full, reduced = (0,a+b+e), (a,a+e)
        assert all(reduced[0] <= x+a for x in full)
        assert all(x <= y+b for x,y in zip(full,reduced))
        assert reduced[1]-min(reduced)==e and full[1]-min(full)==a+b+e
        n+=1
    return n


if __name__ == '__main__':
    print(json.dumps({'finite_contracts':check_contracts(),'controls':check_witnesses(),
                      'sharpness_triples':check_sharpness(),'labeled_lift':check_labeled_lift()},sort_keys=True,indent=2))
