# CRGC v0.2.1 experimental handoff review

24 November 2026 · Private working note

**The first experiment should answer one question.** When batteries can charge and discharge independently, does temporarily grouping their operating modes shorten the time to a physically admissible schedule of specified quality? Chat reports that the full linear relaxation (LP) already matched the full mixed-integer optimum on all 24 development cases. This makes a validated LP policy an essential comparator. [Experiment register](https://chatgpt.com/space/page_dfa9a6f1ac5081919df0487eb77df505)

## What the integrated manuscript adds

| Addition | Evidence in v0.2.1 | Limit on the claim |
|---|---|---|
| Exact aggregation for interchangeable integer-state batteries, C-E002 | Chat reports 255,440 aggregate transitions, 1,087,666 after quotienting by permutations and 5,399,145 with labeled assets. The 24 aggregate objectives matched the independently formulated mixed-integer model within numerical checks. | These are transition counts for particular implementations. An elapsed-time advantage requires a matched solver comparison. |
| Fixed proportional dispatch, C-E003 | With positive fixed weights, constant efficiencies, no self-discharge and individual terminal SOC equal to initial SOC, summing each device’s dynamics gives total discharge equal to its round-trip efficiency times total charge, in class-level units. Two different efficiencies force zero throughput. | Terminal tolerances replace the equality with a necessary upper bound. Individual allocation changes the feasible set. The claim concerns a particular restriction, even for colocated assets. |
| Shared operating modes with individual power and state of charge (SOC), C-E003 | Shared modes matched the full objective in 12/12 heterogeneous development cases. Two-class proportional control missed in all 12, with mean regret 308.95 synthetic cost units. Idling was feasible on all 24 development cases. | The manuscript gives an instance where a shared mode makes the problem infeasible. The 24 LP objective ties leave the admissibility of the returned LP schedules to be checked. |

These numerical results are attributed to Chat’s manuscript and source. This review did not replay Chat’s evidence archive. The added VP/VNP proof review is a separate line of work. Neither the battery identities nor the proposed timing comparison depends on the claimed separation. [Source versions](https://chatgpt.com/space/page_c22eca223fc88191a109ba88e518d954)

## Two controls that can falsify an implementation

**A cost match can hide an inadmissible battery instruction.** In Chat’s two-hour example, two identical batteries each start and end at 1.5, both efficiencies are 0.8, and required grid import is 0.36 each hour. Average the published feasible schedule with the schedule obtained by swapping battery labels. Each battery now charges 0.50 and discharges 0.32 in each hour. At relaxed mode 0.5 both power bounds hold. Each SOC stays fixed because `0.8 × 0.50 − 0.32 / 0.8 = 0`. Fleet import is `2 × (0.50 − 0.32) = 0.36`. The average preserves the linear cost and all grid measurements. A validator must reject simultaneous charging and discharging on each battery. This exact-arithmetic witness is a test input. Which solutions the LP solver returned on the 24 cases remains unverified here.

**Balanced endpoints need a label convention.** Take two ideal unit-capacity batteries with unit rate and positive cycling cost `k`. Prescribe labeled endpoints `(1,0)` and `(0,1)` one period apart. Both endpoints are balanced, and total energy stays at one. The aggregate zero-movement schedule costs zero. Meeting the labeled endpoints requires two units of movement and costs `2k`. W03-B should specify endpoints compatible with one fixed balanced lift, or explicitly allow an endpoint set invariant under permutations. Include this mutation alongside the positive test with identical endpoints. The archived C-E002 cases used identical endpoints.

Both controls ran using exact arithmetic. The checker rejected simultaneous operation in all four device-hours of the averaged schedule and accepted both original schedules. At `k = 1`, exhaustive one-period enumeration returned a minimum cost of 2 for swapped labeled endpoints and 0 when endpoint permutations were admissible. To replay, run `python3 replay_controls.py` with Python 3.9 or later. All inputs are in the file. [Replay code](replay_controls.py) · [Recorded results](handoff_controls.json)

## Decision rules for Work

- **W03-A.** Freeze held-out instances, separate ordinary and forced-opposing-mode cases, and fix the tuning budget, absolute and relative gap tolerances, deadlines and fallback before opening the holdout. Compare adaptive grouping with full HiGHS MILP, full LP with validation and timed recovery, fixed shared modes, proportional grouping and symmetry reduction where applicable. Record time from model construction to the first independently validated schedule and to the prescribed gap. A feasible reconstructed schedule supplies the upper bound `U` for minimization. Use a lower bound `L` valid for the unrestricted model. Include construction, presolve, validation, recovery and fallback in elapsed time. Count every deadline miss and every infeasible returned action. Idling itself fails the fixed-import witness above. If a simpler comparator reaches the same quality and admissibility as fast on a cohort, that cohort supplies no speed advantage for adaptive grouping.
- **W03-B.** Formalize the integer balanced lift, objective preservation, efficiency obstruction and terminal-tolerance bound with all endpoint and integrality hypotheses. Record the pinned build, theorem statements, axioms and negative controls. A tested numerical checker and a compiled theorem need separate evidence entries.
- **W03-C/D/E.** The remaining specifications cover static AC optimal power flow, unit commitment and rolling forecast-aware battery/load control. Work’s archived W-E05 already records a forecast-aware rule matching LP service on all four synthetic profiles. W03-E needs a common forecast issue time for both policies. C and D need explicit network and contingency models before any security-constrained claim.

## Source custody and claim identifiers

Both parent TeX files match the SHA-256 identifiers in v0.2.1 Appendix A. The Work evidence ZIP is available locally. All 40 entries listed in its checksum manifest matched in both the archive and its expanded copy. This verifies file identity. The integrated TeX reviewed here has SHA-256 `1c2f0b09f16b6833707d6d8e61ab4f48b8ceeb03e20bc9019aea82c99c175a9e`. [Work evidence packet](../CRGC_v0.2_research_packet.zip)

The original v0.1 TeX was recovered from the version register and matched its recorded SHA-256. The original ten-page PDF is also present in that register. [Recovered TeX](CRGC_Whitepaper_v0.1.tex) · [Version register and original PDF](https://chatgpt.com/space/page_c22eca223fc88191a109ba88e518d954)

Use branch and version with every claim ID. The integrated Appendix B reuses Work’s `C16` through `C20` for different claims. For example, `Work v0.2/C16` identifies a reported external VP/VNP audit, while `Integrated v0.2.1/C16` identifies the balanced storage lift. A join on `C16` alone would silently attach unrelated evidence. [Original Work claim ledger](../CRGC_v0.2/claim_evidence_map.csv)

**Campaign status at handoff.** W03-A through W03-E are queued. This review checked the handoff, the historical files and the arithmetic controls. It did not launch a solver campaign or a Lean build.
