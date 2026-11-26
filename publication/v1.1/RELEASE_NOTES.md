# VP–VNP formalization audit v1.1

Justin Candler · November 26, 2026 · [Version 1.1 DOI](https://doi.org/10.5281/zenodo.24572841)

This edition corrects the audit's explanation of the C.1 midpoint inequality and clarifies the scope of the field and resource bounds. The archived review-team Linux run remains the source of the full five-declaration comparison in Lean and nanoda. The new checks below were performed by the review team. [Original Linux run](https://github.com/nousentllc/VP-VNP-Review/actions/runs/45691617731)

## Changes from v1.0

- **C.1, pp. 17–18.** The published exposition divided by the mesh parameter twice in prose. Dividing the finite slope inequality once gives the stated midpoint bound. The error estimate permits the joint choice `A = T²`. The choice `A = T` leaves the intercept term without uniform decay. Exact rational checks covered 5,664 scalar configurations, including 480 with zero endpoint radius.
- **Field restrictions, p. 40.** The endpoint table now makes explicit that the exact and Laurent-series approximation lower bounds for the Hamiltonian cycle polynomial hold over every field. The corresponding permanent bounds apply in characteristic other than two.
- **J.4, p. 38.** The text spells out the scale and exponent assumptions for the common cutter and the two K.5 cost estimates. The estimates improve listing and traversal bounds. The final separation exponent is unchanged.
- **Evidence, pp. 40–42.** The same 24 finite controls reproduced identical output on the historical candidate tag, the reviewed Git snapshot and the deposited v1.0 software. All 530 selected evidence files matched across the software deposit, the report archive and the reviewed snapshot. Native Lean 4.33.1 accepted both J.4 declarations using retained publisher imports and reported the three recorded axioms. [Reviewed Git snapshot](https://github.com/nousentllc/VP-VNP-Review/tree/f7d16f5fd48ac0ffcfe50c3828778dc7c97a27c3) · [Software deposit](https://doi.org/10.5281/zenodo.24569000)

## Independent checks still open

- An outside operator has yet to provide a fresh Linux Tier 1/2 replay with the pinned inputs, dated transcripts and hashes. The historical five-endpoint run and the fresh targeted J.4 replay are review-team evidence. [Reproduction instructions](https://github.com/nousentllc/VP-VNP-Review/blob/f726d3a7608e31b5c88804764b6e65c203179d42/REPRODUCE.md)
- An independent human algebraic-complexity reviewer has yet to assess whether the formal statements and definitions capture the advertised mathematical claims. The detailed geometry in F.2–F.5, machine accounting in J.3–J.4 and complete approximate accelerator in N.4 retain further human-reading obligations. [Review invitation](https://github.com/nousentllc/VP-VNP-Review/issues/1)
- The publisher's response to the proposed K.3 canonical-code and I.1 zero-weight-trace wording changes remains open. These observations concern stronger prose interpretations. The accepted formal endpoints stand. [Publisher issue](https://github.com/anthropics/formal-math/issues/57)

The report includes all 63 historical dossier entries. The exact v1.0 report and its original accompanying software retain their own records. The Software Heritage identifier for the exact software tree was unconfirmed at the release check. [Report v1.0](https://doi.org/10.5281/zenodo.24568943) · [Original software](https://doi.org/10.5281/zenodo.24569000)
