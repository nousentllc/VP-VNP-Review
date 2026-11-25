# Pass 13C · Why half a coefficient is enough for the permanent projection

**Edition 10, November 25, 2026.** Proposition E.1 represents an arbitrary finite grid sum over a commutative ring in which 2 is invertible. This is a weighted coefficient identity. Several permutations can contribute to one assignment, and contributions can cancel. Corollary E.2 and Lemma E.3 transfer a candidate permanent circuit to the network polynomial. The point of the transfer is that a lower bound for the latter then constrains *every* candidate permanent circuit of the specified size. [E.1, pp. 31–32](../primary/vp-vnp/paper.pdf#page=31) · [E.2, p. 32](../primary/vp-vnp/paper.pdf#page=32) · [E.3, p. 33](../primary/vp-vnp/paper.pdf#page=33)

## 1. Objects and direction

Let finite incidences $I$ carry surjections $v:I\to V$ and $w:I\to K$. Each incidence $n$ has four entries $W_n(a,b)$ in a commutative ring $R$. Each left class chooses one bit $x_v$, each right class one bit $r_w$. The desired value is

$$
 Z(W)=\sum_{x:V\to\{0,1\}}\sum_{r:K\to\{0,1\}}
        \prod_{n\in I} W_n(x_{v(n)},r_{w(n)}).
$$

Choose $h\in R$ satisfying $2h=1$. For *every* $S\ge3|I|$ the proposition constructs a matrix of order $S$ whose permanent equals $Z(W)$. The factor three counts the rows and columns allocated to each incidence. Subsequently, over $R=F[Y]$, put the entries of this matrix into the generic $S\times S$ permanent in the independent variables $X_{ij}$. This gives the grid polynomial as a formal polynomial in $Y$. The equality covers all inputs jointly, even over a finite field. [Ring-valued proposition](../primary/vp-vnp/Paper/Grids.lean#L23) · [Generic polynomial evaluation](../primary/vp-vnp/Nc/PermValiant.lean#L59)

## 2. A coefficient calculation that enforces the local choice

For an arbitrary matrix $M$ with column variables $t_j$, the coefficient of $\prod_jt_j$ in $\prod_i\sum_j M_{ij}t_j$ equals its permanent. The chosen column in each row has to be distinct. Hence we may calculate modulo the ideal $(t_j^2:j)$, because later multiplication by further polynomials cannot remove a repeated factor. This is the quotient with $t_j^2=0$. Replacing this relation by Boolean idempotence $t_j^2=t_j$ would allow a repeated column to survive. The column variables here serve coefficient extraction and are distinct from the bits that index the sum. [Coefficient lemma](../primary/vp-vnp/Nc/PermCoeff.lean#L95) · [Square ideal](../primary/vp-vnp/Nc/PermCoeff.lean#L119)

Choose one cycle of a permutation $\sigma$ on every $v$-fibre, and one cycle of $\rho$ on every $w$-fibre, with fixed points on singleton fibres. Label the three columns at $n$ by $A_n,B_n,C_n$ and abbreviate $A'=A_{\sigma n}$. The first two rows at $n$ have linear forms $h(A_n+B_n+A'-C_n)$ and $A_n+B_n-A'+C_n$. Their product in the square-zero quotient equals

$$
 h\bigl[(A_n+B_n)^2-(A'-C_n)^2\bigr]
 =2h(A_nB_n+A'C_n)=A_nB_n+A'C_n.
$$

This uses commutativity and $2h=1$. It holds even when $A'=A_n$. Label the first monomial $s_n=1$ and the second $s_n=0$. The $A$-column is chosen at $n$ or $\sigma n$ accordingly. For a given $m$, its number of uses in the labelled expansion is $\mathbf1_{s_m=1}+\mathbf1_{s_{\sigma^{-1}m}=0}$. Requiring exactly one yields $s_m=s_{\sigma^{-1}m}$ everywhere, precisely one bit per $v$-fibre. The unused column at $m$ is $C_m$ if $s_m=1$ and $B_m$ if $s_m=0$. [Local matrix](../primary/vp-vnp/Nc/PermGrid.lean#L122) · [Identity including coincident columns](../primary/vp-vnp/Nc/PermCoeff.lean#L143)

Write $D_m(1)=C_m$ and $D_m(0)=B_m$. The third row has two labelled families, with options $b=1$ and $b=0$:
$$
 \sum_{a=0}^1 W_n(a,1)D_n(a)+\sum_{a=0}^1 W_{\rho n}(a,0)D_{\rho n}(a).
$$
The destination $m$ equals $n$ or $\rho n$ respectively. To select the one column remaining there, the choice of $a$ is forced to be $s_m$. Each destination must receive one third row. The same predecessor count now forces $b$ to be constant on the $\rho$-cycles. Thus for every surviving bit pair, the map from third rows to destinations is a bijection, $b_n=b_m$, and the product over destinations is $\prod_m W_m(s_m,b_m)$. This explains the shifted subscript $W_{\rho n}$ and why the auxiliary choice contributes multiplicity one *after* the first two rows have been combined. Surjectivity identifies the invariant functions on incidences with all assignments of bits to the label sets. With an unused bit, summation over that bit would add a factor of two. Padding by $M\oplus I_{S-3|I|}$ only adds fixed unit choices. If $I$ is empty, surjectivity forces both label sets to be empty. The single empty assignment, the empty permanent and every identity padding all have value 1. [Global slot bijection](../primary/vp-vnp/Nc/PermGrid.lean#L67) · [Unique auxiliary choice and reindexing](../primary/vp-vnp/Nc/PermGrid.lean#L175) · [Fibres](../primary/vp-vnp/Nc/PermSum.lean#L51) · [Padding](../primary/vp-vnp/Nc/PermPad.lean#L68)

## 3. Exact diagnostics and a characteristic boundary

**Single incidence.** All fibres are singletons. In column order $A,B,C$ the actual matrix after coincident terms are added is
$$
 \begin{pmatrix}
  2h&h&-h\\
  0&1&1\\
  0&W(0,1)+W(0,0)&W(1,1)+W(1,0)
 \end{pmatrix}.
$$
Its permanent is $2h\sum_{a,b}W(a,b)$. With $W(0,0)=1$ and all other entries zero, the desired value is 1. Choosing $h=1$ gives 2 over the rationals and 0 in characteristic two. In fact, when $2=0$ the first row of *each incidence* is $h$ times its second, whatever $h$ is. Over such a field the permutation signs coincide, hence permanent equals determinant. For every nonempty incidence set this gadget therefore gives zero identically. This is a counterexample to dropping the half assumption for this formula. E.1 makes no claim that all other encodings must fail. The M.2 Hamiltonian-cycle construction uses its own weight-preserving correspondence and works in characteristic two. [Formal field hypothesis](../primary/vp-vnp/Paper/Grids.lean#L59) · [M.2 comparison](12b-hamiltonian-projection.md)

**Two incidences sharing both bits.** Set $W_0=((1,2),(3,4))$ and $W_1=((5,6),(7,8))$ with rows indexed by $a$ and columns by $b$. Then $Z=5+12+21+32=70$. Treating the bits at the two incidences independently gives $10\cdot26=260$. Enumerating all $6!$ raw permutation terms of the actual matrix gave total positive weight 213 and negative weight $-143$. Their sum is 70 and padding to order 7 preserves it. The raw permutations cannot be read as one positive contribution per bit assignment. For a test with overlapping rather than identical fibres, use $v=(0,0,1)$, $w=(0,1,0)$ and $W_n(a,b)=4n+2a+b+1$. The exact grid and permanent are 2924. Changing the shifted coefficient $W_{\rho n}$ to $W_n$ while leaving the destination unchanged gives 2860. [Exact enumeration and controls](../checks/pass13c_permanent.py)

## 4. Why the substitution fits the circuit model

An entry of the weighted third row is an additive sum involving incidences from one $w$-fibre, since $w(\rho n)=w(n)$. The affine form of E.1 asks for one optional coordinate $o(k)$ for every right class $k$. All four weights at each incidence of that fibre are in the span of $1,Y_{o(k)}$ (or constants when the coordinate is absent). This subspace is additively closed, so a matrix entry is constant or $aY_i+b$. Dropping the common-coordinate condition can yield $Y+Z$ in one entry of even the singleton matrix, by choosing $W(0,1)=Y$ and $W(0,0)=Z$. The original ring-valued identity still holds in this example. The single-coordinate guarantee is what changes. Since each assignment term multiplies $|I|$ affine factors, $Z(W)$ has degree at most $|I|$. Variables can repeat. Two shared-bit incidences with weight tables $((Y,0),(1,Y+1))$ and $((1,2),(Y,Y-1))$ give $Y^2+2Y-1$. [Quantifier order](../primary/vp-vnp/Nc/Rate/Defs.lean#L39) · [Fixed-fibre closure](../primary/vp-vnp/Paper/Grids.lean#L59)

For a circuit of $s$ gates computing $\mathrm{PERM}_S$, replace each input variable by its affine entry. The list $a,Y_i,aY_i,b,aY_i+b$ uses five gates counting constants and the variable. An old sum or product takes the already substituted outputs of its old predecessors. Storing these at position $5j+4$ in a zero-indexed layout preserves every later use of gate $j$. Padding the blocks gives a $5s$-gate circuit for $Z$. The three in $3|I|$ concerns the input matrix order. The five in $5s$ concerns the size of a circuit supplied for that matrix order. An independently proved lower bound $L$ on the grid circuit size implies $s\ge L/5$. Neither constant by itself gives a superpolynomial bound. [Gate transformation](../primary/vp-vnp/Nc/PermValiant.lean#L70)

For an E.2 clause of weight $u$ with nonempty literal list, the $b=0$ term is 1, and $b=1$ contributes $(u-1)\prod_j\mathbf1_{\text{literal }j}$. Weight $u-1$ is charged to the first literal exactly once. The sum over $b$ is $u$ when the clause is satisfied and 1 otherwise. E.3 puts one clause at each node for each possible bit pattern on its incident edges. Exactly one pattern per node is active. For $k\ge2$, $\ell\ge1$, there are $k2^{(k-1)\ell}$ clauses, each of length $(k-1)\ell$, hence $q=k(k-1)\ell2^{(k-1)\ell}$ incidences and the projected network polynomial has degree $k$. E.1 allows $S\ge3q$; E.3 uses the looser uniform condition $S\ge3k^3\ell2^{k\ell}$. At $k=2$, $\ell=1$ there are four literals: a $12\times12$ matrix suffices for the construction of $X_{1,0}X_{2,0}+X_{1,1}X_{2,1}$ while the displayed E.3 threshold is 96. [Clause construction](../primary/vp-vnp/Paper/Grids.lean#L83) · [Circuit caller](../primary/vp-vnp/Paper/Flat.lean#L132)

## 5. Verification and boundary

From the repository root run `python3 checks/pass13c_permanent.py`. The standard-library program constructs the actual signed rows, compares exact permanents with direct bit sums, and checks every one-hot table assignment on all one- and two-incidence fibre partitions (68 cases). It includes seven specializations of the repeated-variable example and three odd-characteristic checks. The finite cases guard the conventions used in the preceding derivation. The ring-valued identities and labelled-slot counting above supply the general argument.

**Complete polynomial controls at six specified topologies.** For a fixed grid of $n$ incidences over the rationals, regard the $4n$ table entries as independent indeterminates. Both the permanent and the grid sum are homogeneous of degree $n$ in those entries: exactly one weight comes from each third row on the matrix side. This does not presuppose that individual tables occur once in each raw term. Write $D$ for the difference and let $|\alpha|=n$. Then
$$
  \left(\prod_i\alpha_i!\right)[W^\alpha]D
    =\sum_{\beta\le\alpha}(-1)^{n-|\beta|}
       \left(\prod_i\binom{\alpha_i}{\beta_i}\right)D(\beta).
$$
Indeed the $\alpha_i$-fold forward difference removes polynomials of degree below $\alpha_i$ in coordinate $i$. Among degree-$n$ monomials only $W^\alpha$ survives every difference; it yields the displayed factorial product. The program computes both sides of the projection at these integer tables using exact fractions and checks each resulting coefficient difference. All 512 coefficients vanished: 4 singleton linear coefficients, 36 quadratic coefficients at each of the four two-incidence fibre configurations, and 364 cubic coefficients at the three-incidence overlapping configuration above. This also checks spurious monomials that might use two weights from the same incidence. It proves the polynomial identity at those six topologies over the rationals independently of the general source proof.

A fresh Lean 4.33.1 run rebuilt all 12 project modules ending at Paper.Grids against nine revision-checked external repositories. All rebuilt source files match the archived publisher tree. The final readback succeeded for ten declaration types and seven axiom lists. Each queried list contained only propext, Classical.choice and Quot.sound. This run covers the square ideal, the local identity, the permutation test, the full E.1 grid, E.2, and affine substitution. The pinned proof objects for the target can be rebuilt in a fresh directory using the existing runner and a prebuilt checkout of the dependencies from the publisher's lock file. The E.3 caller is read at its original declaration in this track. E.4 and the branch estimates have their own evidence. [Queries](../checks/pass13c_permanent.lean) · [Replay output](../checks/pass13c_permanent_replay.json) · [Replay runner](../checks/pass09_endpoint_replay.py)

```sh
python3 checks/pass09_endpoint_replay.py --target-module Paper.Grids \
  --query-file checks/pass13c_permanent.lean --mathlib "$MATHLIB_DIR" \
  --lean "$PINNED_LEAN" --output /tmp/pass13c_permanent_replay.json
```
