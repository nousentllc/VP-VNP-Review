"""Generate the frozen one-hour, AC-side synthetic BESS cases."""
import json
import numpy as np
from common import ROOT, DESIGN, save


def make_case(seed, n, t, cohort):
    rng = np.random.default_rng(np.random.SeedSequence([seed,n,t,DESIGN['A']['cohorts'].index(cohort)]))
    cap = rng.uniform(3, 9, n)
    power = cap * rng.uniform(.23,.43,n)
    ec, ed = rng.uniform(.81,.98,n), rng.uniform(.84,.98,n)
    initial = cap*rng.uniform(.36,.64,n)
    wear = rng.uniform(.5,2,n)
    floor = rng.uniform(.03,.19,(n,t))*cap[:,None]
    avail = np.ones((n,t))
    tol = cap * (.035 if seed in (1102, 8297) else 0.)
    load = rng.uniform(.9*n,1.45*n,t)
    upper = np.full(t,2.4*n)
    lower = np.zeros(t)
    price = rng.uniform(16,85,t)
    ramp, previous = .9*n, float(load[0])
    charge, discharge = np.zeros((n,t)), np.zeros((n,t))
    if cohort == 'interchangeable':
        cap[:], power[:], ec[:], ed[:], initial[:], wear[:] = 6, 2, .93, .94, 3, 1
        floor[:] = .65
        tol[:] = 0.
    if cohort == 'negative_outage':
        price[::3] = -rng.uniform(65,150,len(price[::3]))
        avail[np.arange(n), np.arange(n) % t] = 0
        floor[:,t//2] = .96*initial
        upper = np.maximum(load,1.18*n)
    if cohort == 'forced_opposition':
        # Pairwise devices of different sizes. Member-specific cycles are constructed,
        # disclosed to every method as the same pre-existing safe policy.
        cap[:], power[:], initial[:], floor[:], tol[:] = 4., 1., 2., .15, 0.
        ec[:] = np.repeat(rng.uniform(.74,.86,n//2),2)
        ed[:] = np.repeat(rng.uniform(.78,.88,n//2),2)
        for i in range(n):
            charge[i,i%2::2] = .9
            discharge[i,(1-i%2)::2] = .9*ec[i]*ed[i]
        load[:] = 0.
        lower = (charge-discharge).sum(axis=0)
        upper = lower.copy()
        previous = lower[0]
        ramp = .5*n
        price[::3] = -25.
    return dict(id=f'{cohort}_{n}x{t}_{seed}', seed=seed, cohort=cohort, n=n, t=t,
                capacity=cap, power=power, eta_c=ec, eta_d=ed, initial=initial,
                floor=floor, terminal_tolerance=tol, wear=wear, availability=avail,
                load=load, grid_lo=lower, grid_hi=upper, price=price, ramp=ramp,
                previous=previous, fallback_charge=charge, fallback_discharge=discharge)


def generate():
    config = DESIGN['A']
    for split in ['development','holdout']:
        cases = [make_case(seed,n,t,cohort) for n,t in config[split+'_sizes']
                 for seed in config[split+'_seeds'] for cohort in config['cohorts']]
        save(ROOT/'inputs'/f'battery_{split}.json', cases)


if __name__ == '__main__':
    generate()
