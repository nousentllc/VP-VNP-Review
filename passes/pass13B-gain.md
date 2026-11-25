# Pass 13B · Why a contracting price yields a saving at every tower stage

**Question.** G.2 must supply one finite menu of exact rerouting identities before the size or contents of the network are known. It also has to leave enough slack for the quadratic load in H.2 to contract at rate $1/2$. Following each choice shows that the Poincaré constant is fixed before the group dimension $h$, whereas the packet scale $a_1$ can depend on $h$. The final stage condition contains the first constant and omits the packet scale. This quantifier order is what makes the choice possible. [F.6, pp. 40–41](../primary/vp-vnp/paper.pdf#page=40) · [G.1–G.2, pp. 42–43](../primary/vp-vnp/paper.pdf#page=42) · [H.2, pp. 45–48](../primary/vp-vnp/paper.pdf#page=45)

## 1. Obtain a constant before choosing the group

The hypothesis on $K$ says that one pair $\mu\ge 2,\ 1\le s<\sqrt\mu$ works for all $K$-prices on the binary $\mu\times\mu$ matrices. The inequality $D(\mu)\le sD(1)$ compares root-mean-square distances under full-rank and rank-one shifts. A price here belongs to the manuscript's tensor-defined class of distances. In particular, the distance of a spectral point on a wire is admissible. Distances may vanish at distinct parties. [Definition D.1](../primary/vp-vnp/Paper/Alternative.lean#L43) · [Prices, including the zero price](../primary/vp-vnp/Nc/Price/Basic.lean#L111)

Let $U_h$ be the upper unitriangular group over $\mathbb F_2$, $b=|U_h|=2^{h(h-1)/2}$, and $x_j=1+E_{j,j+1}$. Its Cayley graph joins $g$ to $x_jg$ for $0\le j<h-1$. For $h=lu,\ l\ge2$, F.6 gives
$$
 b^{-2}\sum_{g,k} w(k,gk)^2
 \le C_{\rm P}\sum_{j<h-1} b^{-1}\sum_k w(k,x_j k)^2
$$
for **all** prices $w$. Here both $u$ and $C_{\rm P}$ depend only on the contracting data. To see why, let $C_{\rm win}(n)$ denote the preceding window bound, with $C_{\rm win}(n)=o(n^2)$. Fix $u\ge2$ large enough that $4C_{\rm win}(3u)\le(u-1)^2/32^2$. Realize $w$ in the complete CAT(0) price space provided by C.3 and act on maps from $U_h$ into that space by translations. Write $P_i$ for projection to maps fixed by the generators in the length-$2u$ window starting at $iu$. There are $k=l-1$ windows, and $\Phi(z)=\sum_i d(z,P_i z)^2$. The contraction and near-orthogonality estimates of F.2–F.5 enter here as geometric inputs. [Choice of $u$](../primary/vp-vnp/Paper/Groups.lean#L1070) · [F.6 statement and geometric inputs](../primary/vp-vnp/Paper/Groups.lean#L1085)

Set $c=1/4,\ \delta=1-2c=1/2$. The barycenter $z'$ of the projections satisfies $\Phi(z')\le(1-\delta/k)\Phi(z)$ and $k\,d(z,z')^2\le \Phi(z)-\Phi(z')$. If $\Phi(z)>0$, put $\Delta=\Phi(z)-\Phi(z')\ge\delta\Phi(z)/k$. It follows that
$$
 d(z,z')\le\sqrt{\Delta/k}\le\frac{\Delta}{\sqrt{\delta\Phi(z)}}
 \le\frac{2}{\sqrt\delta}\left(\sqrt{\Phi(z)}-\sqrt{\Phi(z')}\right).
$$
When $\Phi=0$ the same conclusion follows from the second inequality. Summing successive steps telescopes. Although the geometric factor $1-\delta/k$ tends to one as $k$ increases, the total length bound $2\sqrt{\Phi(z)/\delta}$ holds independently of $k$. Completeness gives a limit fixed by every window, hence by the group. Each generator occurs in at most two windows. Its action through a common fixed point gives a distance at most twice the distance to that point. Squaring and multiplying the three factors gives $4\cdot(4/\delta)\cdot2 C_{\rm win}(2u)=32C_{\rm win}(2u)/\delta=C_{\rm P}$. This is the uniformity G.2 uses. [One averaging step](../primary/vp-vnp/Paper/Groups.lean#L839) · [Cauchy limit and fixed points](../primary/vp-vnp/Paper/Groups.lean#L870) · [Multiplicity of windows and resulting bound](../primary/vp-vnp/Paper/Groups.lean#L987)

The map $(g,k)\mapsto(k,gk)$ lists all ordered pairs; rerouting counts unordered off-diagonal pairs. Each undirected Cayley edge has two orientations. For all pairs $\mathcal P$, Cayley edges $\mathcal E$, $\alpha=2/[b(b-1)]$, and $\beta=2/b$, the conversion gives
$$
 \sum_{e\in\mathcal P}\alpha w_e^2\le C'_0
       \sum_{\nu\in\mathcal E}\beta w_\nu^2,\qquad C'_0\in\mathbb N,\quad C'_0\ge 2C_{\rm P}+1 .
$$
The finite-population factor is $b/(b-1)\le2$. Fix $C_1=4C'_0$, then take a multiple $h$ of $u$ with $h\ge\max(3,2u,4(1+8C_1))$. This fixes the graph before any law or circuit is chosen. [Ordered-to-unordered conversion](../primary/vp-vnp/Paper/Laws.lean#L53) · [Explicit admissible multiple](../primary/vp-vnp/Paper/Laws.lean#L425)

## 2. Pass from quadratic distances to a finite menu

Use the dual norms $\|n\|_{\mathcal P}^2=\sum n_e^2/\alpha$ and $\|y\|_*^2=\sum y_\nu^2/\beta$. Put $Z_1=\|\mathbf1\|_{\mathcal P}, Z_2=\|\mathbf1\|_*, c_0=\sqrt{C'_0}\ge1$. Choose an integer $a\ge4(Z_1+Z_2)+1$. For $x\ge0,\ \|x\|_{\mathcal P}\le1$, set $\sigma=\lceil ax\rceil$. The old load satisfies $\|\sigma\|\le a+Z_1$, so it belongs to a finite integral norm ball. The implementation permits every old load in this larger ball. Let $R=a+Z_1$, and, for a fixed price, $W=(\sum_{\mathcal E}\beta w_\nu^2)^{1/2}$. Cauchy–Schwarz and F.6 give
$$
  \langle\sigma,w\rangle\le R(\sum_{\mathcal P}\alpha w_e^2)^{1/2}
      \le c_0 RW.
$$
If $W>0$, the real edge vector $y_\nu=c_0 R\beta w_\nu/W$ has norm $c_0R$ and achieves $\langle y,w\rangle=c_0RW$. Its coordinatewise ceiling $B$ still dominates the old charge and has $\|B\|_*\le c_0R+Z_2$. If $W=0$, zero load suffices. The admissible integral edge ball is finite, since positive coordinate weights bound every coordinate separately. Thus the **same menu** $\mathcal B$ works for all prices while its maximizing member may depend on the price. [Weighted duality and rounding](../primary/vp-vnp/Nc/Price/Norm.lean#L109) · [Finite menus](../primary/vp-vnp/Paper/Laws.lean#L241)

An analytic test of the quantifier order takes the load $(1,1)$ and menu $\{(2,0),(0,2)\}$. At every nonnegative test vector $w$, $w_1+w_2\le2\max(w_1,w_2)$. Evaluating the two coordinate test vectors rules out a single member that wins on both. This test concerns support functions. No claim that these vectors constitute a particular G.2 law is needed. [Independent checks](../checks/pass13b_gain.py)

## 3. Why duality yields an exact tensor identity

For an integral load $D$, $W^D$ is the tensor product of $D_e$ two-dimensional equality wires on each pair $e$. By A.2, for every spectral point $\varphi$,
$\log_2\varphi(W^D)=\langle D,d_\varphi\rangle$. Thus the previous inequality supplies $\forall\varphi\,\exists B\in\mathcal B:\varphi(W^\sigma)\le\varphi(W^B)$. All these tensors take value one on the all-zero assignment, satisfying A.6's nonvanishing conditions. For every $\varepsilon>0$ and all sufficiently large $q$, A.6 gives a cover of $W^{q\sigma}$ by $m\le2^{\varepsilon q}$ restrictions of product tensors. Term $i$ uses multiplicities $v_{iB}\in\mathbb N$ with $\sum_B v_{iB}=q$, hence the channel lengths $L_{i\nu}=\sum_B v_{iB}B_\nu$. To cover a tensor here means to express it **exactly as a sum** after separate linear maps at each party in each term. [A.6, pp. 20–21](../primary/vp-vnp/paper.pdf#page=20) · [Formal statement](../primary/vp-vnp/Paper/Gauges.lean#L560) · [Its application to wires](../primary/vp-vnp/Paper/Laws.lean#L120)

The combinatorial part of A.6 explains why the term count is subexponential in this quantified sense. Write $T=W^\sigma,\ A_B=W^B,\ \eta=2^{-\varepsilon/2}$. A certificate replaces $T^k$ by terms $T^{r_i}\prod_B A_B^{v_{iB}}$ with $r_i+|v_i|=k$, charging weight $\eta^{|v_i|}$ per term. If no certificate for the unit has total weight below one, taking infima defines a normalized upper functional. A.5 then provides a single spectral point with $\varphi(A_B)\le\eta\varphi(T)$ for every $B$. Since $\eta<1$ and $T\ne0$, this contradicts the preceding spectral inequality. A certificate with total weight below one therefore exists. Every summand exchanges at least one $T$, since an unexchanged summand alone would weigh one. Recursively replace whenever $k$ copies of $T$ remain; the number of unexchanged copies strictly drops along each finite branch and the sum of weights never increases. At the leaves it is at most one, and each leaf weighs at least $\eta^q$. There are at most $\eta^{-q}$ leaves. Each has fewer than $k$ leftover copies of $T$, replaceable at a fixed cost using a nonzero $A_B$. Absorb the fixed multiplier into $2^{\varepsilon q/2}$ for large $q$. A fixed $\varepsilon$ is already sufficient for G.2. [A.5 contradiction](../primary/vp-vnp/Paper/Gauges.lean#L601) · [Strict replacement](../primary/vp-vnp/Paper/Gauges.lean#L452) · [Counting residual copies](../primary/vp-vnp/Paper/Gauges.lean#L512)

The separate local maps in each term are the desired tables. In coordinates an equality wire kills assignments disagreeing at the two ends. Summing surviving coordinates leaves one shared binary word for each near edge. Evaluating the local maps on fixed input bits and these shared words is exactly G.1's product of local table entries summed over words and term indices. All agreeing external bits give one, so $m>0$. Local tables may have signed coefficients. The finitely many tables generate a subring $A\subset K$ of finite type over $\mathbb Z$; applying any map $A\to R$ preserves the entire finite sum-product identity. [From restrictions to tables](../primary/vp-vnp/Nc/Price/Law.lean#L50) · [From words to slots](../primary/vp-vnp/Nc/Price/LawF.lean#L27) · [Nonempty index set](../primary/vp-vnp/Paper/Laws.lean#L287) · [Finite ring and base change](../primary/vp-vnp/Paper/Laws.lean#L162)

## 4. Pay the label and close both clauses of G.2

Choose $\varepsilon>0$ with $\varepsilon Z_2\le a/4$, for instance $a/[4(Z_2+1)]$. For each of the finitely many old loads A.6 supplies a threshold $q_0(\sigma)$. One integer $q=1+\sum_\sigma q_0(\sigma)$ exceeds them all. Take $a_1=aq$, label width $\lambda=\lceil\varepsilon q\rceil+1$, and store the same term index on every channel. For every term of every law, Minkowski and $\sum_Bv_{iB}=q$ give
$$
 \|\lambda\mathbf1+L_i\|_*
 \le\lambda Z_2+q[c_0(a+Z_1)+Z_2]\le2c_0aq .
$$
For the second inequality, $c_0Z_1+Z_2\le c_0a/4$. Also
$\lambda Z_2\le(\varepsilon q+2)Z_2\le aq/4+2Z_2\le 3c_0aq/4$ because $q\ge1$. Thus the output norm is at most $\sqrt{C_1}a_1$, **including the common label on every edge**. If $\|n\|\le a_1t,\ t>0$, choose $x=n/(a_1t)$, $\sigma=\lceil ax\rceil$. The law has $q\sigma_e$ slots, so $n_e\le tq\sigma_e$ componentwise. At $t=0$ every off-diagonal coordinate is zero; the formal load has an unused diagonal part. This proves the two promises under the stated inputs. [Uniform power and coding](../primary/vp-vnp/Paper/Laws.lean#L264) · [Slot count](../primary/vp-vnp/Paper/Laws.lean#L318) · [Overhead budget](../primary/vp-vnp/Paper/Laws.lean#L376)

Squaring the output bound gives the integer test $b\sum_\nu(\lambda+L_{i\nu})^2\le G_1$, with $G_1=2C_1a_1^2=8C'_0 a_1^2$. The tower uses $\rho=1/2$ in $1+8C_1\le\rho^2h$. Its actual load update, for $V_j$ current vertices, $Q_j$ normalized edge load, and $d=\sqrt{C_1}a_1/b$, is
$$
 Q_{j+1}\le Q_j/2+dV_{j+1}.
$$
The good-outcome condition, choice of least-loaded type, and the $b$-to-one tower are additional inputs to this recurrence. Since $V_j=bV_{j+1}, b\ge4$, $Q_{j+1}+dV_{j+1}\le(Q_j+dV_j)/2$. At $J$ levels with $b^J$ comparable to the starting size $M$, the halving gives exponent $\gamma=1/\log_2 b$, positive for this fixed field data. A size-dependent $a_1$ would reenter through $d$; the finite menu was fixed before $M$. The cut theorem consumes laws chosen in this order. [Integer test](../primary/vp-vnp/Paper/Laws.lean#L456) · [Stage hypotheses and update](../primary/vp-vnp/Nc/Tow/Load3.lean#L279) · [H.2 quantifiers and exponent](../primary/vp-vnp/Paper/Tree.lean#L1628) · [Cut caller](../primary/vp-vnp/Paper/Cuts.lean#L570)

## 5. Independent controls and remaining obligations

On $U_3$ the two generators give an eight-cycle. A cut price assigns distance one precisely when two vertices lie on opposite sides; it is the wire distance of flattening rank across that bipartition (A.1–A.2, p. 19). There are 28 unordered pairs and 8 edges. For 128 cuts modulo complementation, including the zero price, the maximal nonzero energy ratio is $8/7$. Indeed, a cut of size $k$ crosses $k(8-k)\le16$ old pairs and at least two cycle edges unless it is constant. The ratio is at most $(16/28)/(2/4)=8/7$, with equality for four consecutive vertices. Choose four consecutive vertices and occupy 15 of the 16 pairs crossing that cut. Exactly two near edges cross. With $R=\sqrt{28\cdot15}$ and the sharp **finite cut-family** ratio $8/7$, the ideal load on either is $\sqrt{60}$: rounding down gives $14<15$, rounding up gives $16$. This exercises the support-vector step at its own admissible real comparison constant; $h=3$ does not satisfy G.2's degree condition. It supplies no field classification. In a separate scalar test, $u=4,C_1=8$ first meet the sufficient stage inequality at $h=260$. If the constant had grown as $C_1(h)=h/32$, no $h$ could have met it. [Flattening and wire values, p. 19](../primary/vp-vnp/paper.pdf#page=19) · [Exact controls](../checks/pass13b_gain.py) · [Scalar Lean proof](../checks/pass13b_budget.lean) · [Independent replay receipt](../checks/pass13b_budget_results.json)

**Reproduction.** From the review root run `python3 checks/pass13b_gain.py`. It checks 3,968 cut-price/load combinations and 972 budget choices. The independent scalar proof imports only Mathlib. With the pinned Lean 4.33.1 executable and the built libraries from the publisher manifest on `LEAN_PATH`, run `lean -j1 -DautoImplicit=false checks/pass13b_budget.lean`. The Lean check reported only `propext`, `Classical.choice`, and `Quot.sound` for each of the two independent declarations. [Independent Lean receipt](../checks/pass13b_budget_results.json)

The construction assumes the field's contracting hypothesis. The local G.2 construction is existential. It gives neither numerical values of its laws for an identified comparison field nor a uniform search algorithm producing them. The independent mathematical review still relies on A.5's spectral separation, F.2–F.5's window geometry and H.1's tower. Deriving the remaining circuit and cut estimates is a distinct obligation. [Earlier law-value audit](12a-contracting-laws.md) · [Theorem H.1, p. 44](../primary/vp-vnp/paper.pdf#page=44)
