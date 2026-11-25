"""Pass 14A. Test mixed-cut rank, the geometric ledger, and its strict numerical margin."""
from fractions import Fraction
from itertools import combinations, product
import json


def matrix_rank(matrix):
    rows = [list(map(Fraction, row)) for row in matrix]
    rank = 0
    for column in range(len(rows[0])):
        pivot = next((j for j in range(rank, len(rows)) if rows[j][column]), None)
        if pivot is None:
            continue
        rows[rank], rows[pivot] = rows[pivot], rows[rank]
        scale = rows[rank][column]
        rows[rank] = [value/scale for value in rows[rank]]
        for j in range(rank + 1, len(rows)):
            coefficient = rows[j][column]
            rows[j] = [x-coefficient*y for x, y in zip(rows[j], rows[rank])]
        rank += 1
        if rank == len(rows):
            break
    return rank


def support_and_witness():
    # A singleton selector is a nonzero vector. Its matrix rank is one.
    e00, e11 = [[1, 0], [0, 0]], [[0, 0], [0, 1]]
    total = [[x+y for x, y in zip(a, b)] for a, b in zip(e00, e11)]
    assert matrix_rank(total) == 2 and matrix_rank(e00) == matrix_rank(e11) == 1
    ranks = []
    for isolated in [1, 2]:
        other = [i for i in range(3) if i != isolated]
        ranks_at_cut = []
        for linked in [1, 2]:
            remaining = 3 - linked
            matrix = [[0]*4 for _ in range(2)]
            for i, word in enumerate(product(range(2), repeat=2)):
                for bit in range(2):
                    t = [0]*3
                    t[isolated] = bit
                    t[other[0]], t[other[1]] = word
                    matrix[bit][i] = int(t[0] == t[linked] and t[remaining] == 0)
            ranks_at_cut.append(matrix_rank(matrix))
        ranks.append(ranks_at_cut)
    assert ranks == [[2, 1], [1, 2]]
    return ranks


def signed_selector():
    # T_j[x,y,z] with z contracted by a j-dependent functional. An independent
    # direct word expansion checks that the chosen reordering acts on both ends.
    tensors = [
        [[[1, -1], [1, 2]], [[-2, 0], [3, 1]]],
        [[[2, 1], [-1, 0]], [[-1, 2], [-2, 0]]],
    ]
    maps = [(1, 1), (-1, 1)]
    def entry(j, a, b):
        return sum(s*w for s, w in zip(tensors[j][a][b], maps[j]))
    count = 0
    for n in (1, 2, 3):
        words = list(product(range(2), repeat=n))
        for xs in words:
            for ys in words:
                by_type = 0
                for zero_count in range(n+1):
                    rep = (0,)*zero_count + (1,)*(n-zero_count)
                    acc = 0
                    for w in words:
                        if w.count(0) != zero_count:
                            continue
                        permutation = sorted(range(n), key=w.__getitem__)
                        term = 1
                        for j, i in zip(rep, permutation):
                            term *= entry(j, xs[i], ys[i])
                        acc += term
                    by_type += acc
                target = 1
                for a, b in zip(xs, ys):
                    target *= entry(0, a, b)+entry(1, a, b)
                assert target == by_type
                count += 1
    return count


def hub_directions():
    # Compare the coordinate-by-coordinate construction to the crossing count.
    choices = 0
    for k in range(2, 11):
        for size in range(k+1):
            if not k <= 3*size <= 2*k:
                continue
            for subset in combinations(range(k), size):
                signs = [1 if i in subset else -1 for i in range(k)]
                t = [0]*k
                for i,j in combinations(range(k), 2):
                    if signs[i] != signs[j]:
                        t[i] += signs[i]
                cross = sum(a*b for a,b in zip(t, signs))
                norm_sq = sum(x*x for x in t)
                assert cross == size*(k-size)
                assert k*norm_sq >= cross**2 and 9*cross >= 2*k*k
                choices += 1
    return choices


def margin_controls():
    f = Fraction
    margin = f(4,81)-f(3,2000)-f(1,100)-f(1,10000)
    middle = f(4,9)+f(1,1000)
    assert 12*margin-middle == f(1073,135000)
    # A scalar point obeying each pre-elimination hypothesis. Its rational
    # entries need not be realizable by a spectral point and an actual circuit.
    k, root, ell, logL = 4, 2, 200, 138
    N, delta = k*(k-1)//2, f(1,1000*k)
    wire = N*(1-delta)
    outside = N-f(4*k,81)+2*N*delta
    inside = f(4,9*root)+delta
    label = root+delta
    slack = k*label+ell*outside+inside*logL-ell*wire
    assert slack >= 0 and f(ell*k*root,12) < logL < f(ell*k*root,11)
    return {"strict_margin": str(12*margin-middle), "relaxed_budget_slack_at_log2L_138": str(slack)}


def main():
    print(json.dumps({"flattening_rows_B_C_columns_AB_AC": support_and_witness(),
                      "signed_tensor_power_entries": signed_selector(),
                      "balanced_hub_directions": hub_directions(),
                      **margin_controls()}, indent=2))


if __name__ == "__main__":
    main()
