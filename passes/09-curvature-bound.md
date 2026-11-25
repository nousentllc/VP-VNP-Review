# Pass 9 · Theorem C.1 and the curvature bound

**November 24, 2026.** Theorem C.1 supplies the squared midpoint inequality used in Proposition C.3. We reconstructed the implication from the fan estimates and Lemma C.2, including the constants hidden in the manuscript. For fixed original points, the final error is at most $(6D^2+6Db+b^2)/T$, where $b=w(z,m)$. The fan and its averaged seminorm can change with $T$. The proof uses the same fan sequence for every comparison length at a given $T$. [Manuscript, Appendix C, pp. 25–28](../primary/vp-vnp/paper.pdf#page=25) · [Pinned proof of C.1](../primary/vp-vnp/Paper/Fan.lean#L987)

## Statement and scope

Fix a field $K$, a $K$-price $w$, and points $x,v,m,z$. Write $|uv|=w(u,v)$. Assume $|xm|,|vm|\le D$ and $|xv|=2D$. Nonnegativity and the triangle inequality force $D\ge0$ and $|xm|=|vm|=D$. Put

$$
b=|zm|,\qquad H=D+b,\qquad
\Gamma=b^2-\tfrac12(|zx|^2+|zv|^2).
$$

C.1 asserts $\Gamma\le-D^2$. An ordinary metric with a midpoint need not satisfy this. In the plane with the maximum-coordinate metric take $x=(-1,0),v=(1,0),m=(0,1),z=(0,-1)$. The hypotheses on distances hold with $D=1$, yet the proposed upper bound for $|zm|^2=4$ would be zero. This independent example isolates the need for a property of prices. C.1 itself does not assert that a midpoint exists for every pair. [Statement, p. 25](../primary/vp-vnp/paper.pdf#page=25) · [C.3’s use of C.1](08-price-space-completion.md)

## The two-sheet fan and its four estimates

Fix an integer $T\ge2$ and $\theta=1/T$. For each $n$, the proof uses A.8 first to place the two sets of intermediate points $\gamma_i$ along the paths from $x$ and $v$ to $m$, then to place $G(i,j)$ between each $\gamma_i$ and $z$. Within each application the newly added points use a common random threshold. A.8 bounds distances by expectations while preserving old distances. In particular, upper bounds in both directions along the segment add up to $L_i=|z\gamma_i|$, so the triangle inequality forces $|zG(i,j)|=\rho L_i$ exactly, with $\rho=1-j\theta/n^2$. Also $0\le L_i\le H$ and $n^2|L_{i+1}-L_i|\le D$. The formal construction calls the finite-random-map form of A.8. [Eq. (C.3), p. 27](../primary/vp-vnp/paper.pdf#page=27) · [Shared thresholds](../primary/vp-vnp/Paper/Fan.lean#L60) · [Fan](../primary/vp-vnp/Paper/Fan.lean#L166)

On each sheet use $0\le i<n^2$, $0\le k<n$, and $j=i+k+n$. Extend the construction by clamping indices to their ranges and pull back the price scaled by $n^2$ to obtain $W_n$. The two sheets have equal weight. For fixed $T$, choose the family of fans once. Write $E$ for the fixed free-ultrafilter limit of box means, $\Lambda_2=E(L^2)$, $\nu(g)^2=E[W_n(P,P+g)^2]$, and $N(g)=\inf_{S\ge1}\nu(Sg)/S$. For fixed displacement $g$, the step bound $W_n(P,P+g)\le (2D+b)\|g\|_1$ keeps these means finite. Fixed translations preserve $E$ because their boundary fractions vanish. Subadditivity gives the same $N$ as the limit along integer multiples. The construction requires no ordinary convergence of the unaveraged sequence of fans. [Averaging, pp. 25–26](../primary/vp-vnp/paper.pdf#page=25) · [Invariant mean](../primary/vp-vnp/Nc/Cat/Mean.lean#L183) · [Seminorm](../primary/vp-vnp/Paper/Means.lean#L133)

| Direction | Estimate | Reason |
|---|---|---|
| $(1,0)$ | $N(1,0)\ge D$ | The two sheets reach a common end. Their endpoint distances from $x$ and $v$ sum to at least $2D$. The finite-box initial offset is $O(1/n)$. Translation and Cauchy–Schwarz give the bound for every $S$. [Claim (i)](../primary/vp-vnp/Paper/Fan.lean#L592) |
| $(1,-1)$ | $N(1,-1)^2\le D^2(1-\theta+\theta^2)$ | This step keeps $j$ fixed. Its length is at most $(1-\theta i/n^2)D$. The average of $i/n^2$ tends to $1/2$. Taking $S=1$ suffices. [Claim (ii)](../primary/vp-vnp/Paper/Fan.lean#L655) |
| $(0,1)$ | $N(0,1)^2\le \theta^2\Lambda_2$ | A single vertical step costs at most $\theta L_i$ after rescaling. Square and average. [Claim (iii)](../primary/vp-vnp/Paper/Fan.lean#L725) |
| $g_A=(1,-1-A)$ | $N(g_A)^2\ge A^2\theta^2\Lambda_2+A\theta\Gamma-4A\theta^2DH$ | Compare distances to $z$, square, and telescope the squared lengths along each sheet. The same lower bound must survive every $S$ in the infimum. [Claim (iv)](../primary/vp-vnp/Paper/Fan.lean#L910) |

## Why the first averaging step keeps the error controlled

Fix integers $A,S\ge1$ before taking the box mean. For $n\ge\max(2,AS)$ the vertical positions $j$ and $j-AS$ are admissible. With $L=L_i$ and $L'=L_{\min(i+S,n^2)}$, reverse triangle gives
$$
W_n(P,P+Sg_A)\ \ge\ \left|n^2\rho(L'-L)+AS\theta L'\right|.
$$
On squaring, the identity $2L'(L'-L)-(L'^2-L^2)=(L'-L)^2$ controls the mixed term even when $L'-L<0$. Replacing $\rho$ by one in the signed squared-length difference loses at most $4A\theta^2S^2DH$, since $0\le1-\rho\le2\theta$ and $n^2|L'^2-L^2|\le2SDH$. This leaves the lower bound $(AS\theta)^2L'^2 + AS\theta n^2(L'^2-L^2)-4A\theta^2S^2DH$. [Pointwise displacement](../primary/vp-vnp/Paper/Fan.lean#L484) · [Difference bound](../primary/vp-vnp/Paper/Fan.lean#L759) · [Square estimate](../primary/vp-vnp/Paper/Fan.lean#L813)

**Independent finite-box derivation.** Put $M=n^2$, $f(i)=L_i^2$ on a sheet and extend $f$ constantly after $M$. For $S\le M$ the box mean of $M(f(i+S)-f(i))$ is $S f(M)-\sum_{r=0}^{S-1} f(r)$. Its difference from $S(f(M)-f(0))$ has absolute value at most $DH S(S-1)/n^2$, by the step bound on $L$. The two endpoint differences average to $\Gamma$. Likewise the box averages of $L'^2$ and $L^2$ differ by at most $2DHS/n^2$. Thus at fixed $A,S$ their means give $S\Gamma$ and $\Lambda_2$ respectively. The formal proof only needs the one-sided telescope bound. After division by $S^2$ the remaining loss is $4A\theta^2DH$, independent of $S$. A lower bound valid for every $S$ passes to $N(g_A)^2$ by taking square roots when the bound is positive and using nonnegativity otherwise. [One-sided formal telescope](../primary/vp-vnp/Paper/Fan.lean#L792) · [Taking the mean](../primary/vp-vnp/Paper/Fan.lean#L860)

**Stress test.** The finite-box $o(1)$ above need not be uniform in $S$. For the scalar test profile $L_i=1+i/n^2$ and $S=n$, the magnitude of the boundary discrepancy is $(n-1)/n+(n-1)n(2n-1)/(6n^4)$, tending to one. This tests the telescope using an admissible Lipschitz profile. The proof fixes $S$, takes the mean, then uses the resulting inequality for every $S$. Exact rational checks reproduced 102 clamped-profile cases and five growing-step identities. [Reproduce the finite checks](../checks/pass09_fan_boundary.py)

## From the four estimates to the curvature bound

Lemma C.2 obtains the parallelogram identity for $N$ from the crossing inequality (B.2). It first passes (B.2) to the mean by Cauchy–Schwarz and then to $N$ along integer multiples. Its own large-vector argument bounds the remaining error by $36(N(a)+N(b))^2/R$ for fixed vectors $a,b$. Applying the upper parallelogram bound to $a+b,a-b$ supplies the reverse inequality by homogeneity. C.1 needs only the upper half. [Lemma C.2, pp. 26–27](../primary/vp-vnp/paper.pdf#page=26) · [Transfer to the mean](../primary/vp-vnp/Paper/Means.lean#L96) · [Large-vector bound](../primary/vp-vnp/Paper/Means.lean#L392) · [Parallelogram law](../primary/vp-vnp/Paper/Means.lean#L442)

Put $p=N(1,0)^2$, $q=N(1,-1)^2$ and $\beta=\theta^2\Lambda_2$. The second difference of $N(1,-1-\ell)^2$ equals $2N(0,1)^2\le2\beta$. Hence $\psi(\ell)=N(1,-1-\ell)^2-\ell^2\beta$ has nonincreasing increments for $\ell\ge-1$. The slope from $-1$ to $0$ is $q-p+\beta$, including the $+\beta$ because $\psi(-1)=p-\beta$. Therefore $\psi(A)\le q+A(q-p+\beta)$. Estimate (iv) gives
$$
 A\big[\theta\Gamma-4\theta^2DH-(q-p+\beta)\big]\le q.
$$
At fixed $T$ the same $q,p,\Lambda_2$ serve every integer $A$. A positive bracket would fail for any integer $A$ larger than $q$ divided by that bracket. Equivalently the temporary error after normalization is $q/(A\theta)$, which vanishes at fixed $T$. Substitution of (i) and (ii) then gives
$$
\theta\Gamma-4\theta^2DH\le D^2(-\theta+\theta^2)+\theta^2\Lambda_2.
$$
Finally divide by the positive $\theta$ and use $0\le\Lambda_2\le H^2$. For **every** integer $T\ge2$,
$$
\Gamma+D^2\ \le\ \frac{D^2+H^2+4DH}{T}
=\frac{6D^2+6Db+b^2}{T}.
$$
The numerator depends only on the original four points. Taking $T\to\infty$ gives $|zm|^2\le (|zx|^2+|zv|^2)/2-D^2$. Neither $D$ nor $b$ is used as a divisor, so the argument also covers the zero-distance cases. The two endpoint limits remove different errors. Before either endpoint limit, $q\le D^2$ also gives the explicit remainder $D^2T/A+(6D^2+6Db+b^2)/T$. A joint choice with $A/T\to\infty$ would suffice at this stage. Setting $A=T$ leaves $q/(A\theta)=q$, for which the intermediate bound alone supplies no decay. [Concavity and the fixed-$T$ argument, p. 28](../primary/vp-vnp/paper.pdf#page=28) · [Formal endpoint](../primary/vp-vnp/Paper/Fan.lean#L929) · [Uniform final bound](../primary/vp-vnp/Paper/Fan.lean#L987)

## Independent verification

Lean 4.33.1 checked five declarations in a focused file using the pinned Mathlib dependencies. The first replays the publisher’s discrete concavity lemma. Four review lemmas check the fixed-$T$ slope argument, the explicit mesh remainder, its limit, and the combined implication with quantifiers $\forall T\ge2\;\exists(f,\phi,\Lambda)\;\forall A$. The fan inequalities and the second-difference bound enter as hypotheses. Each declaration reports only `propext`, `Classical.choice`, and `Quot.sound`. Separately, the finite-box check exercises the boundary identity above. The C.1 fan construction, the crossing inequality, C.2 and the full `Paper.Fan` module were source-traced or used at their stated interfaces. Full independent replay remains open. [Endpoint checks](../checks/pass09_endpoint.lean) · [Environment, hashes, results and reproduction](../checks/pass09_endpoint_results.json) · [Publisher’s discrete concavity lemma](../primary/vp-vnp/Nc/Cat/Window.lean#L127)

## What this changes for the review

C.3 may now use C.1 on the strength of a reconstructed conditional derivation. The remaining upstream questions include the spectral extension behind A.8 and the crossing inequality (B.2) used by C.2. The midpoint estimate alone supplies no circuit-size lower bound. The paper reaches circuits through C.3, D.2 and the two branches of the lower-bound argument. For pass 10, trace Proposition A.7 into A.8 and check whether one extension preserves **all** old distances and satisfies **all** requested upper bounds simultaneously. [A.7 and A.8, pp. 21–22](../primary/vp-vnp/paper.pdf#page=21) · [Finite spectral construction](../primary/vp-vnp/Paper/Prices.lean#L160) · [Finite random maps used by the fan](../primary/vp-vnp/Paper/Prices.lean#L414)
