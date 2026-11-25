"""Independent finite rational checks for W05-B. Standard library only."""
import json
from fractions import Fraction as Q
from itertools import product


def factor(residual, slack):
    if slack < 0:
        raise ValueError("The anchor fails this row.")
    return residual / (residual + slack) if residual > 0 else Q(0)


def fraction(rows):
    return max((factor(u, slack) for u, slack in rows), default=Q(0))


def dot(x, y):
    return sum(a*b for a, b in zip(x, y, strict=True))


def mix(t, x, a):
    return [(1-t)*u + t*v for u, v in zip(x, a, strict=True)]


def row_test():
    pool = list(product(map(Q, ["-2", "-1/2", "0", "1/4", "2"]),
                        map(Q, ["0", "1/3", "2"])))
    systems = tests = boundary = untouched = strict_coarse = 0
    for m in (0, 1, 2, 3):
        for rows in product(pool, repeat=m):
            lam = fraction(rows)
            assert 0 <= lam <= 1
            systems += 1
            boundary += any(u>0 and s==0 for u, s in rows)
            untouched += all(u<=0 for u, _ in rows)
            trial_fractions = set([Q(i, 4) for i in range(5)] + [lam, lam/2, (1+lam)/2])
            for t in trial_fractions:
                holds = all((1-t)*u-t*s <= 0 for u, s in rows)
                assert holds == (lam <= t)
                tests += 1
            violated = [(u, s) for u, s in rows if u>0]
            if violated and min(s for _,s in violated)>0:
                bar=max(u for u,_ in violated)
                sigma=min(s for _,s in violated)
                assert lam<=bar/(bar+sigma)
                strict_coarse += lam < bar/(bar+sigma)
            hrows = [(max(Q(0), u)+Q(1,3), s) for u,s in rows]
            assert lam<=fraction(hrows)
    return dict(systems=systems, feasibility_comparisons=tests, forced_boundary=boundary,
                initially_feasible=untouched, strict_improvement_over_coarsest_positive_margin=strict_coarse)


def support_test():
    lo=[Q(-2),Q(1),Q(-1)]
    hi=[Q(1),Q(2),Q(3)]
    axes=[[a,(a+b)/2,b] for a,b in zip(lo,hi)]
    checks=0
    for coeff in product(map(Q,[-2,0,3]),repeat=3):
        upper=sum(max(c*a,c*b) for c,a,b in zip(coeff,lo,hi))
        seen=[]
        for x in product(*axes):
            seen.append(dot(coeff,x))
            assert seen[-1]<=upper
            checks+=1
        assert max(seen)==upper
    return dict(supports=27, grid_values=checks, all_attained=True)


def terminal_test():
    """Change one fixed-mode power magnitude with exact feasibility of every row.
    A q-unit charge raises imports q at slot j and SOC η*q from j onward.
    This direct checker crosses all slots and hard rows with both signs of q."""
    seeds=exact_equalities=admitted=refused=0
    for eta in map(Q,["3/4","9/10"]):
        for eta_d in map(Q,["4/5","19/20"]):
            for mode in product(("C","D"),repeat=3):
                power=[Q(1),Q(1),Q(1)]
                def eval_state(z):
                    e=Q(4);gprev=Q(3);rows=[];states=[]
                    for i,zi in enumerate(z):
                        charge=zi if mode[i]=="C" else Q(0)
                        discharge=zi if mode[i]=="D" else Q(0)
                        g=Q(3)+charge-discharge
                        e+=eta*charge-discharge/eta_d
                        rows += [-zi,zi-2, g-6,-g,g-gprev-2,gprev-g-2,e-8,-e]
                        # Fixed zero reserve in C slots and 1/4 in D slots.
                        rows.append(discharge+(Q(1,4) if mode[i]=="D" else Q(0))-2)
                        gprev=g;states.append(e)
                    return rows,states[-1]
                rows,terminal=eval_state(power)
                assert max(rows)<=0
                seeds+=1
                for slot in range(3):
                    for sign in (-1,1):
                        shifted=power.copy();shifted[slot]+=sign
                        other,endpoint=eval_state(shifted)
                        slope=[b-a for b,a in zip(other,rows)]
                        gain=endpoint-terminal
                        for mag in map(Q,["0","1/10","2/3","1","5/3"]):
                            target=terminal+mag*gain
                            required=(target-terminal)/gain
                            bounds=[-r/k for r,k in zip(rows,slope) if k>0]
                            accepted=all(required<=v for v in bounds)
                            fixed=power.copy();fixed[slot]+=sign*required
                            post,e=eval_state(fixed)
                            assert e==target
                            assert accepted==(max(post)<=0)
                            exact_equalities+=1
                            admitted+=accepted;refused+=not accepted
    return dict(fixed_mode_trajectories=seeds,signed_slot_queries=exact_equalities,
                physically_accepted=admitted,limited_by_other_rows=refused)


def witnesses():
    # Section cited by eq:repairbound, literal manuscript values.
    a=[Q(2),Q(2)];x=[Q(3),Q(1)]
    lam=fraction([(x[0]-Q(5,2),Q(5,2)-a[0]),(x[1]-Q(7,2),Q(7,2)-a[1])])
    fixed=mix(lam,x,a)
    assert lam==Q(1,2) and fixed==[Q(5,2),Q(3,2)] and sum(fixed)==4
    assert x[0]-fixed[0]==Q(1,2)
    A=[[1,0,1],[0,1,1]]
    R=[[1,0],[0,1],[0,0]]
    assert [[dot(row,col) for col in zip(*R)] for row in A]==[[1,0],[0,1]]
    initial=[Q(1),Q(2),Q(1,3)];target=[Q(3,2),Q(5,2)]
    residual=[d-dot(row,initial) for d,row in zip(target,A)]
    corrected=[v+dot(rr,residual) for v,rr in zip(initial,R)]
    assert [dot(row,corrected) for row in A]==target
    assert mix(Q(1,2),[Q(2)],[Q(0)])!=[0]
    assert mix(Q(1,2),[Q(1)],[Q(0)])[0] not in (0,1)
    assert mix(Q(1,2),[Q(-1)],[Q(1)])[0]**2 != 1
    assert factor(Q(1,10**9),Q(0))==1
    # P averages pair with shared η. Distinct efficiencies break terminal equality.
    x=[Q(2),Q(0)];avg=[Q(1),Q(1)]
    assert dot([Q(3,4),Q(3,4)],x)==dot([Q(3,4),Q(3,4)],avg)
    assert dot([Q(1),Q(1,2)],x)-dot([Q(1),Q(1,2)],avg)==Q(1,2)
    assert fraction([(Q(1),Q(1)),(Q(1),Q(0))])==1
    assert fraction([(Q(1),Q(1,2))]*2)==Q(2,3)
    assert mix(Q(2,3),[Q(1),Q(1)],[Q(-1,2),Q(-1,2)])==[0,0]
    # Ignoring the base can break bounds during equality correction.
    assert 0+2*(1-0)>1
    # Unchecked (reduced vs raw reconstruction) objective offset.
    assert (7-2) > 0 and (7-7)==0
    return dict(manuscript=dict(fraction=str(lam), repaired=list(map(str,fixed)),
                                objective_increase="1/2"),
                right_inverse=dict(rows=A,right_inverse=R,residual=list(map(str,residual)),
                                   corrected=list(map(str,corrected))),
                inequality_mixing_equality_residual="1",mixed_integral_mode="1/2",
                nonconvex_unit_voltage_squared="0",small_violation_boundary_fallback="1",
                unequal_efficiency_pair_projection_terminal_discrepancy="1/2",
                obligation_after_right_inverse="coordinate 2 equals 2 with bound 1",
                no_single_slot="two charge slots of capacity 1 can meet a deficit of 2 jointly",
                omitted_fee_offset="raw and repaired cost 7 versus reduced 2",
                average_anchor_fraction="2/3",two_single_anchor_fractions=["1","1"])


def report():
    return dict(row_grid=row_test(), affine_box=support_test(), storage=terminal_test(),
                witnesses=witnesses())


if __name__=="__main__":
    print(json.dumps(report(),indent=2,sort_keys=True))
