# Edition 12 follow-up · What J.4 supplies to K.5

This audit reads the same publisher revision as Edition 12, `11b6c7e3c927df2658f513b6b68ea7f8929c62c5`. It develops a local strengthening of J.4 under its published hypotheses and traces its effect on two of K.5's cost terms. The open statement-level review asks an algebraic complexity theorist to compare the printed conclusions with `Statement.lean`. That review is pending. [Review invitation](https://github.com/nousentllc/VP-VNP-Review/issues/1).

## From one cutter output to an accelerator call

At a fixed parameter tuple and a size-bounded input, J.3 gives a terminating cutter. Each accepting run supplies a coefficient and an ordered list of smaller instances, with empty bill and bounded accepting time. For a plain parent, every piece is plain and the sum of the run coefficients times the products of the piece values recovers the parent value. J.4 composes these expansions. It multiplies the parent and child coefficients and concatenates the lists. Multiplicity lives in the ordered list, so two copies of the same piece can take different accepting child runs. An empty list contributes the empty product of one. A required child with no accepting run kills that summand. [J.3 and its run contract](https://github.com/anthropics/formal-math/blob/11b6c7e3c927df2658f513b6b68ea7f8929c62c5/vp-vnp/Paper/Cuts.lean#L34-L44) · [Weighted composition](https://github.com/anthropics/formal-math/blob/11b6c7e3c927df2658f513b6b68ea7f8929c62c5/vp-vnp/NS1/Compose.lean#L178-L221).

K.5 uses the J.4 listing guarantee as soon as the description fits. This gives all-run halting for the cutter and a size bound on every returned piece. The old accelerator's run guarantee then applies to each piece. To conclude a value identity, K.5 separately proves the postponed description is plain. J.4 then supplies piece plainness and its weighted sum identity, and the old accelerator supplies its value for each piece occurrence. [K.5 consumer](https://github.com/anthropics/formal-math/blob/11b6c7e3c927df2658f513b6b68ea7f8929c62c5/vp-vnp/NS1/Scale.lean#L65-L121).

## Tighter J.4 bounds from the same induction

Write $v$ for the scale, $H$ for the target plainness exponent and $\tau$ for the input plainness clock. All quotients below are natural-number floor divisions. The final iteration produces one cutter with bounds on the accepting cost $t$, number of pieces $P$ and size $S'$ of each piece. Its polylogarithmic losses are at most $v$. In particular, the proof gives $tv^{48}\le\tau v$, $Pv^H\le\tau v$, and $S'v^{48}\le v^H v$. Since $v>0$ and $H\ge272$, these yield the following simultaneous bounds on that cutter.

| Quantity | Advertised in J.4 | Retained in the follow-up |
| --- | --- | --- |
| Accepting time per cutter run | $\lfloor\tau/v^{24}\rfloor$ | $\lfloor\tau/v^{47}\rfloor$ |
| Pieces per accepting run | $\lfloor\tau v^2/v^H\rfloor$ | $\lfloor\tau v/v^H\rfloor$ |
| Size of each piece | $v^{H-32}$ | $v^{H-47}$ |

The cutoff $v^H$ for **piece plainness** and the code size bound $v^H$ for **the cutter** retain their own meanings. The argument needs the actual outputs of the J.4 induction at the witnesses it constructs. The weaker abstract `CutHyp` by itself gives the published bounds. [Iteration invariant](https://github.com/anthropics/formal-math/blob/11b6c7e3c927df2658f513b6b68ea7f8929c62c5/vp-vnp/NS1/OneCut.lean#L43-L50) · [Final comparisons in the released proof](https://github.com/anthropics/formal-math/blob/11b6c7e3c927df2658f513b6b68ea7f8929c62c5/vp-vnp/Paper/Cuts.lean#L519-L557).

At the K.5 call with $\tau=v^{e+9}$, these estimates give a listing clock $v^{e-38}$ and count $v^{e+10-H}$. The advertised J.4 interface gives $v^{e-15}$ and $v^{e+11-H}$, respectively. Using the existing piece evaluation cost $v^{H-16}$ and its allowance of 30 extra steps per piece, the stronger count gives a traversal bound $31v^{e-6}\le v^{e-5}$ for $v\ge31$. This verifies two terms of the existing round budget. The guess and description costs, full scale transfer and final lower-bound constant have their original accounting. [K.5 parameter substitution and time accounting](https://github.com/anthropics/formal-math/blob/11b6c7e3c927df2658f513b6b68ea7f8929c62c5/vp-vnp/Paper/Next.lean#L65-L144).

## Reproduce the formal check

The two declarations in [J4_Followup.lean](J4_Followup.lean) state the strengthened J.4 conclusion and the K.5 arithmetic implication separately. The first adapts the published J.4 setup and its code-size argument, using the tighter final inequalities. The second is an implication about the listing and traversal terms. [Verification receipt](verification.json).

Use Lean 4.33.1, the publisher source and compiled objects at the pinned revision, and the built standalone Mathlib checkout at the revisions in the publisher's manifest. The [Edition 12 reproduction instructions](https://github.com/nousentllc/VP-VNP-Review/blob/f4839f6797c60e955683d21551ff508a4a236e54/REPRODUCE.md) describe the build. The local check used retained publisher objects and validates the relevant source hashes, exact dependency revisions and axiom readback for both new declarations.

```sh
python3 -B verify.py --project "$PROJECT" --mathlib "$MATHLIB_DIR" \
  --objects "$PUBLISHER_OBJECTS" --receipt verification.json
```

Prepared with OpenAI Codex. The current check verifies the follow-up source against existing imports. The publisher retains attribution for the underlying formalization and the adapted proof setup.
