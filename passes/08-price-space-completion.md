# Pass 8 · How a price survives completion

**November 24, 2026.** Proposition C.3 holds up conditional on the random-point extension A.8, the curvature inequality C.1 and the stated closure properties of prices. The construction gives one complete metric space whose entire distance function is a price over the original field. The two analysis lemmas that pass curvature from a dense subset to the completed space were independently checked in Lean using the publisher’s unchanged declarations and proof bodies. [Manuscript, p. 28](../primary/vp-vnp/paper.pdf#page=28) · [Formal C.3](../primary/vp-vnp/Paper/Curvature.lean#L211)

## The statement D.2 uses

Fix a field $K$, a label set $V$, and a $K$-price $w$ on $V$. C.3 gives a metric space $X$, a map $f:V\to X$, and two properties of $X$. First, $X$ is complete and each pair $x,v$ has one midpoint $m$ satisfying the following inequality for **every** test point $z$.

$$
d(z,m)^2\le \frac{d(z,x)^2+d(z,v)^2}{2}-\frac{d(x,v)^2}{4}. \tag{CN}
$$

Second, the distance function on $X$ is a $K$-price and $d(f(a),f(b))=w(a,b)$ for all original labels. This is the paper’s midpoint formulation of CAT(0). Zero-distance labels may have the same image. D.2 uses the curvature to control quadrangles and the ambient price to pull the filled cube’s distances back to a finite configuration. [CAT(0) definition](../primary/vp-vnp/Nc/Cat/Core.lean#L22) · [D.2 quadrangles](../primary/vp-vnp/Paper/Alternative.lean#L195) · [D.2 cube](../primary/vp-vnp/Paper/Alternative.lean#L857)

## 1. Adding all midpoints compatibly

At one stage, introduce a label for each ordered pair of existing points. One fair bit suffices for all pairs. Outcome zero sends every new label to its first endpoint, and outcome one sends it to its second. A.8 supplies one extended price that preserves every old distance exactly and bounds every new distance above by the corresponding expected distance. For endpoints at distance $L$, both new midpoint legs are at most $L/2$. Their sum is at least $L$ by the triangle inequality, so both legs equal $L/2$. This includes $L=0$. The finite-outcome version covers arbitrarily large old and new label sets. Its spectral input traces to A.7, which the source applies to the product of the old wires to obtain simultaneous preservation of their exponents. [A.8 finite law](../primary/vp-vnp/Paper/Prices.lean#L414) · [Spectral input](../primary/vp-vnp/Paper/Prices.lean#L160) · [C.3 caller](../primary/vp-vnp/Paper/Curvature.lean#L32)

The construction indexes labels by finite midpoint expressions. At stage $n$, it freezes all distances between terms of depth at most $n$. Each pair’s entry is therefore eventually constant, and for a finite list of terms all entries stabilize by the largest term depth. The pointwise limit is a price on the whole term set, agrees with the input on original labels, and contains the chosen midpoint of every term pair. The induction counts depths, so it also works for uncountable $V$. [Terms and depth](../primary/vp-vnp/Nc/Cat/Space.lean#L19) · [Stabilization](../primary/vp-vnp/Paper/Curvature.lean#L58)

**Counterexample to using the expectation itself.** Put old labels $x,y$ at 0 and 2. Under the shared coin, the formal midpoints $p=m_{xy}$ and $q=m_{yx}$ each sit halfway from both old points in the expected-distance table. Yet they are at opposite endpoints in each outcome, so their expected distance is 2. This four-point table satisfies all triangle inequalities. With $m=p,z=q$, (CN) would require $4\le0$. In the price supplied by A.8, C.1 forces $d(p,q)=0$. The distinction between A.8’s upper bound and an equality changes the result. [Exact checks](../checks/pass08_midpoints.py)

## 2. The quotient and the price on the completion

The term table is a pseudometric. If $d(s,t)=0$, the triangle inequality gives $d(s,u)=d(t,u)$ for every $u$. Identifying such pairs preserves the distance table. The source takes the separated metric completion of the pseudometric space directly. Its canonical map preserves distances, has dense image and identifies precisely the zero-distance pairs. This explains why the proposition promises a pullback map, even when the input uses distinct labels for the same point. [Construction and original distances](../primary/vp-vnp/Paper/Curvature.lean#L214)

**Independent finite-label argument.** Take any finite label map $g:F\to X$ and $\varepsilon>0$. Approximate each distinct $g(i)$ by a term image within $\varepsilon/4$, giving one map $i\mapsto t_i$. The triangle inequality bounds every entry’s error by the sum of its two endpoint errors, hence by $\varepsilon/2$. Since the term table is a $K$-price, one spectral point over $K$ and one nonnegative scale approximate its entire pullback on $F$ within $\varepsilon/2$. The same witness therefore approximates every entry of the target table within $\varepsilon$. Repeated labels can use the same approximant, and the argument also covers the empty table. Formally the source chooses an approximating sequence once per completed point. Each whole-table approximation is a pullback of the term price, and pointwise closedness yields the completed price. This only requires convergence on each finite configuration. [Finite-table quantifiers](../primary/vp-vnp/Paper/Prices.lean#L23) · [Closedness](../primary/vp-vnp/Paper/Prices.lean#L81) · [Completion limit](../primary/vp-vnp/Paper/Curvature.lean#L194)

## 3. Why the midpoints converge

On the dense term image, C.1 applies to each chosen midpoint with $D=d(x,v)/2$. For fixed dense endpoints and their fixed midpoint $m$, the set of $z$ satisfying (CN) is closed and contains the dense term image. Hence the same $m$ works for every completed test point. This extension in $z$ occurs before approximating either endpoint. [C.1 invocation](../primary/vp-vnp/Paper/Curvature.lean#L225) · [Density in the test point](../primary/vp-vnp/Paper/Curvature.lean#L166)

For arbitrary $x,v$, let $a_i\to x,\ b_i\to v$ be dense approximations and $m_i$ their chosen midpoints. Write $L_i=d(a_i,b_i)$, $p=d(a_i,a_j)$ and $q=d(b_i,b_j)$. Apply (CN) for pair $j$ at the test point $m_i$. Its distances to $a_j,b_j$ are at most $L_i/2+p,L_i/2+q$. Expanding the squares gives

$$
d(m_i,m_j)^2 \le (L_i^2-L_j^2)/4 + L_i(p+q)/2 + (p^2+q^2)/2.
$$

**Independent estimate.** Interchange $i,j$ and average. The difference of squared lengths cancels.

$$
d(m_i,m_j)^2 \le (L_i+L_j)(p+q)/4+(p^2+q^2)/2.
$$

The $L_i$ are bounded and $p,q$ tend to zero in the joint tail, so the midpoints are Cauchy, including when $x=v$. Completeness supplies a single limit $m$. For any fixed $z$, passing to the limit in (CN) proves the inequality with the same $m$. Testing at each endpoint recovers the exact half-distances. Testing at another midpoint gives zero distance to $m$, establishing uniqueness in the separated space. The publisher uses the bound $d(m_i,m_j)^2\le(2R+4)(p+q)$ in the tail, with $R=d(x,v)+1$ and $p+q\le1$. [Publisher’s Cauchy estimate](../primary/vp-vnp/Paper/Curvature.lean#L96) · [Limit for every test point](../primary/vp-vnp/Paper/Curvature.lean#L178)

**Counterexample to reversing the quantifiers.** If $m$ may depend on $z$, set $m=z$. In every metric space the right side of (CN) is at least $(d(z,x)-d(z,v))^2/4$ by the triangle inequality. The weakened condition is automatic. A complete two-point space at distance one satisfies it and has no midpoint between its points. This is why both the closed-set step and the final limiting step retain one midpoint for all test points. [Two-point check](../checks/pass08_midpoints.py)

## Verification boundary and next obligation

- **Locally replayed.** Lean 4.33.1 checked the publisher’s unchanged proofs of `prop_space_cauchy` and `prop_space_completion` with the unchanged `Cat.CN` declaration and a smaller set of pinned Mathlib imports. Both printed only `propext`, `Classical.choice`, and `Quot.sound`. The SHA-256 of the extracted completion lemmas is `28c77d62e552182d8aaa98cf14435a183348392ff2a31459f420cb45d4a7867c`. The replay script reads the source in this packet. [Reproduce the Lean check](../checks/pass08_completion.py)
- **Source-traced and independently derived.** The A.8 caller, stabilization, zero-distance identification, and same-field finite-table limit were checked against the source. The exact examples exercise the expectation table, the quantifier swap and a finite configuration containing a repeated label. Run `python3 checks/pass08_midpoints.py` from the review root. [Checks](../checks/pass08_midpoints.py)
- **Imported.** A.8’s simultaneous extension and C.1’s curvature inequality remain mathematical inputs to this pass. Independent replay of the full `Paper.Curvature` module and the separation build remains open.

**Pass 9 should start at C.1, pp. 25–28.** Audit how the finite fan built using A.8 produces the endpoint estimate `thm_cn_end`, including its use of the second-difference bound from C.2. Track which bounds are uniform as the fan size increases at fixed $T$, then as $T\to\infty$. The caller needs the precise negative $d(x,v)^2/4$ term in (CN). [Fan construction](../primary/vp-vnp/Paper/Fan.lean#L166) · [Endpoint estimate](../primary/vp-vnp/Paper/Fan.lean#L929) · [Final curvature bound](../primary/vp-vnp/Paper/Fan.lean#L987)
