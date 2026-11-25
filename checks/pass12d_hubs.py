"""Construct the vertices' local matrices and apply them to the full product of equality wires."""

from itertools import product
from math import prod


def placements(size):
    """Restricted growth strings enumerate each partition of the logical vertices once."""
    def extend(prefix):
        if len(prefix) == size:
            yield prefix
        else:
            for site in range(max(prefix, default=-1) + 2):
                yield from extend(prefix + (site,))
    return extend(())


def tuples(shape):
    return product(*(range(n) for n in shape))


def factor(side_dims, rank, salt):
    return {(j, x): (salt * (1 + j) + sum((i+2)*(a+1) for i, a in enumerate(x))) % 7 - 3
            for j in range(rank) for x in tuples(side_dims)}


def routed(dims, left, rank, placement, alpha, beta):
    """Build the product state in each physical-party basis, then apply its local matrices."""
    ends = len(dims)
    cuts = (tuple(i for i in range(ends) if i in left),
            tuple(i for i in range(ends) if i not in left))
    # Each wire has two slots, also when both slots are at a single site.
    edge_sites = [(placement[i], placement[ends + int(i not in left)]) for i in range(ends)]
    edge_sites.append(placement[-2:])
    edge_dims = dims + (rank,)
    sites = range(max(placement)+2)  # include an unoccupied physical site
    slots = [[(e, side) for e, ps in enumerate(edge_sites)
              for side, here in enumerate(ps) if here == q] for q in sites]
    held = [[a for a in range(ends) if placement[a] == q] for q in sites]
    inputs = [list(tuples(tuple(edge_dims[e] for e,_ in sq))) for sq in slots]
    outputs = [list(tuples(tuple(dims[a] for a in aq))) for aq in held]
    mats = []
    for q in sites:
        matrix = {}
        for x, y in product(outputs[q], inputs[q]):
            port = dict(zip(slots[q],y))
            value = prod(int(bit == port[(a,0)]) for a,bit in zip(held[q],x))
            for side, f in enumerate((alpha,beta)):
                if placement[ends+side] == q:
                    value *= f[port[(ends, side)], tuple(port[(a,1)] for a in cuts[side])]
            matrix[x,y] = value
        mats.append(matrix)

    # The actual product of wires kills exactly the basis states with an unequal pair.
    graph_support = []
    for y in product(*inputs):
        ports = {slot: v for sq, local in zip(slots,y) for slot,v in zip(sq,local)}
        if all(ports[e,0] == ports[e,1] for e in range(ends+1)):
            graph_support.append(y)
    values = {}
    for x in product(*outputs):
        flat = {a: bit for aq, local in zip(held,x) for a,bit in zip(aq,local)}
        index = tuple(flat[a] for a in range(ends))
        values[index] = sum(prod(mats[q][x[q],y[q]] for q in sites) for y in graph_support)
    return values


def main():
    checks = 0
    entries = 0
    cases = [
        ((2,2,2), (0,1), 2),  # multi-index left side, every collision partition
        ((2,2), (), 2), ((2,2), (0,1), 2),  # one side empty
        ((), (), 2), ((), (), 0),  # no ends, with positive and zero middle dimension
        ((2,2), (0,), 0), ((0,2), (0,), 2),  # zero middle or zero output index
    ]
    for dims, left, rank in cases:
        ends = len(dims)
        right = tuple(a for a in range(ends) if a not in left)
        alpha = factor(tuple(dims[a] for a in left),rank,2)
        beta = factor(tuple(dims[a] for a in right),rank,3)
        direct = {x: sum(alpha[j,tuple(x[a] for a in left)] *
                         beta[j,tuple(x[a] for a in right)] for j in range(rank))
                  for x in tuples(dims)}
        for placement in placements(ends+2):
            got = routed(dims,left,rank,placement,alpha,beta)
            assert got == direct
            checks += 1
            entries += len(got)

    # Everything is physically co-located, yet x_0 and x_1 remain independently addressable.
    alpha = {(j,(a,)): int(j == a) for j,a in product(range(2),repeat=2)}
    beta = {(j,(a,)): ((2,3),(-1,1))[j][a] for j,a in product(range(2),repeat=2)}
    got = routed((2,2),(0,),2,(0,0,0,0),alpha,beta)
    assert got == {(0,0):2,(0,1):3,(1,0):-1,(1,1):1}
    wrongly_tied_ends = int(0 == 1)*got[0,1]
    wrongly_split_middle = sum(alpha[j,(0,)] for j in range(2))*sum(beta[j,(0,)] for j in range(2))
    assert wrongly_tied_ends == 0 != got[0,1]
    assert wrongly_split_middle == 1 != got[0,0]
    print(f"{checks} placements across {len(cases)} cases, {entries} output entries.")
    print("All-coincident witness: tying distinct ends changes 3 to 0; splitting the middle label changes 2 to 1.")


if __name__ == "__main__":
    main()
