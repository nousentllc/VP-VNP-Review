"""Reconstruct H.1 at h=3, n=1 over the dual numbers and inspect each adjacent-stage route.

Uses Python 3.9+ and the standard library. No publisher functions are imported.
States encode g=B(I+sE), B in GL(3,2), tr(E)=0. Quotienting on the
right by an additive off-diagonal subspace deletes those coordinates of E.
"""
from collections import Counter, defaultdict, deque
from itertools import product
import json


IDENTITY = 0b100010001
WRAP = 1 << 6
GENERATORS = (IDENTITY ^ WRAP, IDENTITY ^ (1 << 1), IDENTITY ^ (1 << 5))
OFF_DIAGONAL = (1, 2, 3, 5, 6, 7)
MASKS = (0, sum(1 << p for p in OFF_DIAGONAL[:3]), sum(1 << p for p in OFF_DIAGONAL))


def matmul(a, b):
    """Multiply two row-packed 3 by 3 matrices over F2."""
    out = 0
    for i in range(3):
        row = 0
        for j in range(3):
            if a & (1 << (3*i+j)):
                row ^= (b >> (3*j)) & 7
        out |= row << (3*i)
    return out


def build_base():
    invertible = {IDENTITY}
    queue = deque([IDENTITY])
    while queue:
        a = queue.popleft()
        for u in GENERATORS:
            value = matmul(u, a)
            if value not in invertible:
                invertible.add(value)
                queue.append(value)
    assert len(invertible) == 168
    return sorted(invertible)


def tables():
    base = build_base()
    indices = {a:i for i,a in enumerate(base)}
    moves = {}
    for idx, a in enumerate(base):
        inverse = next(b for b in base if matmul(a, b) == IDENTITY)
        twist = matmul(matmul(inverse, WRAP), a)
        for k, u in enumerate(GENERATORS):
            moves[idx,k] = indices[matmul(u,a)], (0 if k else twist)
    return indices[IDENTITY], moves


def layers():
    identity_index, moves = tables()
    traceless = [v for v in range(512) if (((v >> 0) ^ (v >> 4) ^ (v >> 8)) & 1) == 0]
    stages = []
    for mask in MASKS:
        chambers = sorted({(i << 9) | (e & ~mask) for i in range(168) for e in traceless})
        neighbours = {}
        for c in chambers:
            base, extra = divmod(c, 512)
            targets = []
            for k in range(3):
                new_base, twist = moves[base,k]
                targets.append((new_base << 9) | ((extra ^ twist) & ~mask))
            neighbours[c] = targets
        assert all(neighbours[neighbours[c][i]][i] == c for c in chambers for i in range(3))
        stages.append(neighbours)
    distances = {identity_index << 9: 0}
    queue = deque(distances)
    while queue:
        c = queue.popleft()
        for d in stages[0][c]:
            if d not in distances:
                distances[d] = distances[c]+1
                queue.append(d)
    assert len(distances) == len(stages[0])
    return stages, max(distances.values())


def chambers_and_orbits(neighbours, omitted):
    unseen = set(neighbours)
    cosets = {}
    lookup = {}
    for seed in sorted(neighbours):
        if seed not in unseen:
            continue
        orbit = {seed}
        queue = deque([seed])
        while queue:
            c = queue.popleft()
            for k, d in enumerate(neighbours[c]):
                if k != omitted and d not in orbit:
                    orbit.add(d)
                    queue.append(d)
        assert len(orbit) == 8
        for c in orbit:
            assert neighbours[c][omitted] not in orbit
            lookup[c] = seed
        cosets[seed] = sorted(orbit)
        unseen.difference_update(orbit)
    return cosets, lookup


def check_stage(lower, upper, mask, omitted):
    low_cosets, low_owner = chambers_and_orbits(lower, omitted)
    top_cosets, top_owner = chambers_and_orbits(upper, omitted)
    def project(c):
        return c & ~mask
    assert set(Counter(map(project, lower)).values()) == {8}
    fibres = defaultdict(list)
    for chi, orbit in low_cosets.items():
        projected = {project(c) for c in orbit}
        omega = top_owner[project(chi)]
        assert projected == set(top_cosets[omega])
        fibres[omega].append(chi)
    assert set(map(len, fibres.values())) == {8}
    host = {}
    for omega, below in fibres.items():
        host.update(zip(sorted(below), top_cosets[omega]))
    children = Counter(host[low_owner[c]] for c in lower)
    assert set(children.values()) == {8} and set(children) == set(upper)
    # Dropping the host bijection maps every lower coset to one upper chamber.
    bad_children = Counter(top_owner[project(c)] for c in lower)
    assert set(bad_children.values()) == {64}

    middle = Counter()
    outer = Counter()
    middle_load = Counter()
    outer_load = Counter()
    old_sq = 0
    lengths = Counter()
    for c, ns in lower.items():
        d = ns[omitted]
        if c > d:
            continue
        a, b = project(c), project(d)
        assert upper[a][omitted] == b and top_owner[a] != top_owner[b]
        old_load = 1 + ((c + 5*d) % 7)
        old_sq += old_load**2
        middle_key = tuple(sorted((a,b)))
        middle[middle_key] += 1
        middle_load[middle_key] += old_load
        # Count the old lower-to-host and host-to-lower segments separately.
        length = 3
        for u, v in ((c,a),(d,b)):
            w = host[low_owner[u]]
            assert top_owner[w] == top_owner[v]
            if w != v:
                key = tuple(sorted((v,w)))
                outer[key] += 1
                outer_load[key] += old_load
                length += 1
        lengths[length] += 1
    assert set(middle.values()) == {8}
    assert max(outer.values()) <= 2
    assert len(upper)*sum(y*y for y in middle_load.values()) <= len(lower)*old_sq
    assert sum(y*y for y in outer_load.values()) <= 4*old_sq
    return dict(selected_type=omitted, lower=len(lower), upper=len(upper),
                selected_edges=sum(middle.values()), middle_fibre=max(middle.values()),
                max_outer_contributors=max(outer.values()),
                bad_host_children=max(bad_children.values()), edge_path_lengths=dict(sorted(lengths.items())))


def signed_relays():
    left, right = (1, -1), (2, 3)
    target = sum(x*y for x,y in zip(left,right))
    for length in [2,3,4,5]:
        value = weakened = 0
        for path in product([0,1],repeat=length):
            weight = left[path[0]]*right[path[-1]]
            value += weight * all(a == b for a,b in zip(path,path[1:]))
            weakened += weight * all(a == b for a,b in zip(path[1:],path[2:]))
        assert (value, weakened) == (-1,0) and value == target
    return {"preserved":target,"omitted_equality":weakened}


def signed_layered_law():
    """Test a signed equality decomposition with index-dependent lengths on one channel."""
    width = 2
    payload_sizes = (0, 0, 1, 2)

    def decode(packets, layers):
        # The last one in the concatenated string is the terminal marker.
        if '1' not in packets:
            return None
        terminal = packets.rindex('1')
        if len(packets) - terminal > width:
            return None
        message = packets[:terminal]
        offset = 0
        indices = []
        for _ in range(layers):
            if offset + 2 > len(message):
                return None
            index = int(message[offset:offset+2], 2)
            offset += 2
            end = offset + payload_sizes[index]
            if end > len(message) or '1' in message[offset:end]:
                return None  # The local law allows only all-zero payloads.
            offset = end
            indices.append(index)
        return indices if offset == len(message) else None

    def local_term(bits, indices, right_end):
        value = 1
        for bit, index in zip(bits, indices):
            if index < 2 and bit != index:
                return 0
            if right_end and index == 3:
                value = -value
        return value

    assert decode('10', 0) == []
    words = list(product(range(2), repeat=width))
    left, right = (2, -3, 5, 1), (-1, 4, 0, 7)
    by_outcome = Counter()
    number_codes = 0
    kernels = Counter()
    for outcome in range(2, 5):
        length = width * (outcome + 1)
        for packet_value in range(2**length):
            indices = decode(format(packet_value, f'0{length}b'), width)
            if indices is None:
                continue
            number_codes += 1
            for a, wa in enumerate(words):
                for b, wb in enumerate(words):
                    term = local_term(wa, indices, False) * local_term(wb, indices, True)
                    kernels[a,b] += term
                    by_outcome[outcome] += left[a]*term*right[b]
    assert number_codes == 4**width
    assert all(kernels[a,b] == int(a == b) for a in range(4) for b in range(4))
    target = sum(x*y for x,y in zip(left, right))
    assert sum(by_outcome.values()) == target
    return dict(packet_width=width, layers=width, boundary_pairs=16, accepted_codewords=number_codes,
                scalar=target, by_outcome=dict(by_outcome), empty_layer_packets=1)


def main():
    stages, diameter = layers()
    counts = [len(stage) for stage in stages]
    assert counts == [43008,5376,672]
    entries = [check_stage(stages[j], stages[j+1], MASKS[j+1], i) for j in range(2) for i in range(3)]
    result = dict(h=3,n=1,b=8,chambers=counts,full_group_diameter=diameter,checks=entries,
                  selected_edge_routes=sum(row["selected_edges"] for row in entries),
                  signed_relay=signed_relays(), signed_layered_law=signed_layered_law())
    print(json.dumps(result,indent=2))


if __name__ == "__main__":
    main()
