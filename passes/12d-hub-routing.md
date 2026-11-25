# Pass 12D supplement · A.3's two hub maps, including coincident parties

**November 25, 2026.** A.3 turns a separated sum on any finite bipartition into a local restriction of a product of wires. Assigning the same location to several parties preserves the construction because a location carries the tuple of all its separate tensor indices. This supplies the general routing step used for both cut bounds in B.3. The paper presents Appendix A under its real-field convention. The pinned theorem assumes an arbitrary field and requires no division, order or characteristic condition. [Manuscript, pp. 18–19 and Figure 4](../primary/vp-vnp/paper.pdf#page=19) · [Formal field and party assumptions](../primary/vp-vnp/Paper/Prices.lean#L151) · [A.3 statement](../primary/vp-vnp/Paper/Prices.lean#L436)

## The local matrices

Let $A=A_L\sqcup A_R$ be the **logical** tensor ends, $X_a$ their finite index sets, and $r$ the number of products in a specified expansion. With $\mathbf x_S=(x_a)_{a\in S}$, the assumed entry formula is
$$
 t(\mathbf x)=\sum_{j=1}^r \alpha_j(\mathbf x_{A_L})\beta_j(\mathbf x_{A_R}).
$$
Write $h_L,h_R$ for the logical hubs. Give each end a wire of alphabet $X_a$ to its hub, and give the middle wire the alphabet $\{1,\ldots,r\}$. A wire has two endpoint indices and contributes the indicator that they agree. The map at an end has matrix entry $[x_a=u_a]$, where $u_a$ is the adjacent wire's end index. At $h_L$ the functional has coefficient $\alpha_{j_L}((v_a)_{a\in A_L})$ on its basis tuple of received end indices and middle index $j_L$. At $h_R$ use $\beta_{j_R}((v_a)_{a\in A_R})$. These finite tables define linear maps on the respective tensor-product spaces. [Source tables](../primary/vp-vnp/Paper/Prices.lean#L443) · [Local maps as matrices](../primary/vp-vnp/Ov/Core/Tensor.lean#L35)

For each fixed output entry the contraction is
$$
 \sum_{\mathbf u,\mathbf v,j_L,j_R}
 \left(\prod_a [u_a=v_a][x_a=u_a]\right)
 [j_L=j_R]\,\alpha_{j_L}(\mathbf v_{A_L})\beta_{j_R}(\mathbf v_{A_R}).
$$
The end indicators leave one possible $\mathbf u=\mathbf v=\mathbf x$. The middle indicator leaves one sum over $j$. This recovers the prescribed value including zero and cancelling terms. The formal proof packages the outer edge labels as the “some” entries of an option-indexed family and the middle label as its “none” entry. Its side-dependence hypotheses on $\alpha,\beta$ guarantee each table depends only on incident inputs. [Dependence at the two hubs](../primary/vp-vnp/Paper/Prices.lean#L457) · [Sum over edge labels](../primary/vp-vnp/Paper/Prices.lean#L477) · [Printed two-further-party version](../primary/vp-vnp/Paper/Prices.lean#L508)

## Which equalities survive a collision?

Allow an arbitrary placement $\xi:A\sqcup\{h_L,h_R\}\to I$. At physical site $q$ take the indexed output tuple $(x_a:\xi(a)=q)$ and the indexed tuple of input half-edges held there. Define its matrix entry to be the product of all logical vertex tables placed at $q$, on their original slots. A vacant site supplies the one-by-one unit. Multiplying over physical sites gives the same vertex-table product as before. The wire product still pairs the two slots of each individual edge. Relabeling the local basis as a tuple is bijective, so the sum stays unchanged.

* If two ends coincide physically, their external indices can still be different.
* If an end coincides with its hub, the outer wire becomes a self-loop. Its two half-edge slots remain separately indexed inside that party. The wire indicator enforces agreement between those two slots only.
* If the hubs coincide, the rank wire also becomes a self-loop. Its indicator still ties $j_L=j_R$. Treating the two labels as independently summable overcounts terms. For positive dimension the self-loop has spectral value one, since the pseudodistance from a party to itself is zero. The intermediate equality constraint still has to be respected by the chosen local map.

This construction is exactly the product of finite wire tensors pushed to the physical parties. The formal network lemma builds the local restrictions from incident-edge dependence and the contraction identity. [Push-forward basis and wire](../primary/vp-vnp/Ov/Core/Tensor.lean#L77) · [Combining co-located local maps](../primary/vp-vnp/Ov/Core/Network.lean#L33) · [Contraction to a restriction](../primary/vp-vnp/Ov/Core/Network.lean#L222)

## Boundaries and downstream use

An empty side has one empty tuple of arguments. Its factor is a scalar for each $j$, supplied by that hub's functional on the middle leg. With both sides empty the value is $\sum_j\alpha_j(())\beta_j(())$. If $r=0$, there are no shared middle assignments and the premise forces the zero tensor. If an end alphabet is empty, there is no full output assignment. The local zero matrices witness the restriction in this case without choosing a default element of that alphabet. The formal network construction handles empty global output or input index types before choosing defaults elsewhere. [Empty-alphabet cases](../primary/vp-vnp/Ov/Core/Network.lean#L40)

For a spectral point, monotonicity gives the cost of the outer wires times the cost of the middle wire. Positive dimension $d$ contributes $d^{w(p,q)}$. The zero-dimensional wire has value zero. Only the **upper bound** by $d^{w(p,q)}$ is used when $d=0$, including when $w(p,q)=0$. Consequently no division by a zero wire dimension is required. B.3's two outer alphabets are nonempty. The same A.3 construction applies to both separations of the selected coefficient, with the appropriate bipartition and bound on the number of product terms. [Wire values at positive and zero dimensions](../primary/vp-vnp/Ov/Core/Wire.lean#L34) · [B.3 spectral caller](../primary/vp-vnp/Paper/Crossing.lean#L28) · [AB cut](../primary/vp-vnp/Paper/Crossing.lean#L45) · [AD cut](../primary/vp-vnp/Paper/Crossing.lean#L71)

A physically merged end and hub can carry a nonidentity local map on the grouped space. B.3 uses ordinary restriction monotonicity at this stage. In E.10 the formal parties distinguish ends and hubs, and the spectral point is pulled back along their possibly coincident geometric positions. Its use of E.7 on tensors with output supported at the ends has these additional hypotheses. [Hub sum from a candidate circuit](../primary/vp-vnp/Paper/Flat.lean#L345) · [Pullback to distinct labels](../primary/vp-vnp/Paper/Rate.lean#L195) · [E.7 caller](../primary/vp-vnp/Paper/Rate.lean#L310)

## Independent checks

The exact control constructs a local matrix for each physical party, enumerates the full product basis of the input half-edges, imposes the graph tensor's per-wire equality indicators, and applies the matrices to that tensor. It compares with a direct sum over the original product decomposition. Seven input cases cover every partition of their logical vertices, giving 116 placements and 600 checked output entries, including one or both empty sides, a zero middle dimension, an empty end alphabet and an extra vacant physical party in every case. A separate all-coincident tensor has entries $\left(\begin{smallmatrix}2&3\\-1&1\end{smallmatrix}\right)$. Identifying two distinct output slots would change its $(0,1)$ entry from 3 to 0. Splitting the middle label would change its $(0,0)$ entry from 2 to 1. [Reproducible Python control](../checks/pass12d_hubs.py)

The earlier fresh pass-10 build compiled the complete 24-module closure for the original publisher module containing A.3. Its recorded list of 13 targeted declaration readbacks covers A.7–A.8. The present supplement contributes a mathematical reconstruction of A.3 and finite matrix checks. The full separation and the remaining mixed-cut circuit decomposition have their own obligations. [Pass-10 build and query list](../checks/pass10_formal_results.json) · [Related E.7–E.11 audit](12c-flat-estimate.md)

Pass 12E subsequently recompiled the full `Paper.Prices` module within the D.2 closure. Its fresh readback of `Paper.lem_hubs` quantifies over the arbitrary placement, partition, two hubs and finite rank used above. [A.3 type and axiom readback](../checks/pass12e_alternative_replay.json)
