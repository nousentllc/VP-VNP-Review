# Independent review of UC starts and numerical bounds

The primary 24 attempted runs yielded one validated group-arm schedule. Unrestricted recovery found it without a grouped start. An LP-repair start was supplied and confirmed on a different date/horizon cell and its incumbent was retained. The only primary 45-second comparison with a validated result in both group and LP arms was RTS August 12 at 48 hours. Group-arm cost exceeded LP-arm cost by 0.14131%. Both unrestricted searches in this comparison started without an incumbent. No primary group-vs-full 45-second cost pair had two schedules. Twenty primary supervisors terminated their workers. Eighteen lacked the first worker checkpoint. This outcome supports a service-availability assessment under the recorded startup guard. It offers very little information about solver search conditional on a successful start.

On the secondary serial replay all 24 jobs reached the worker checkpoint, five were terminated by the supervisor, and each of four arms had a valid schedule in five of its six cells. HiGHS acknowledged four grouped and four LP-repair starts. The acknowledgement included a feasible-start objective matching the validated preparation cost to solver-log rounding precision. The remaining paired workflows each had one no-start unrestricted discovery and one cell without a validated schedule. All eight confirmed transfers had documented solver API success.

| Reported final incumbent on the serial replay | Group preparation | LP repair |
|---|---:|---:|
| Improved by unrestricted search after confirmed start | 3 | 2 |
| Retained from preparation after confirmed start | 1 | 2 |
| Discovered by unrestricted search without a start | 1 | 1 |
| No validated schedule | 1 | 1 |

The costs below compare each workflow's best validated feasible schedule by the same within-worker 45-second deadline. Positive numbers mean group cost was higher. Deployment startup elapsed time is reported separately in supervisor.json. The horizons for a given date share data, and each cell has one run per method.

| Serial date and horizon | Group against direct full (%) | Group against LP preparation (%) |
|---|---:|---:|
| California December 1, 12 h | +0.00053 | +0.00010 |
| California December 1, 48 h | No paired schedules | No paired schedules |
| RTS January 27, 12 h | +0.04345 | +0.04345 |
| RTS January 27, 48 h | −0.50691 | +0.18136 |
| RTS August 12, 12 h | +0.19900 | +0.19900 |
| RTS August 12, 48 h | +0.05297 | +0.15462 |

Across the five matched cells there were zero group wins over both comparators by the prespecified 0.1% threshold. Improvement after a submitted start is attributed to that run's unrestricted search. The causal increment from the start itself cannot be isolated because candidate preparation consumes search time and the CPU environment varied. The serial rerun was motivated by primary startup failures and retains separate denominators.

The audit found 358 cumulative full-model-bound updates across both panels. Their sources were optimal outer LP or unrestricted MIP stages, never a paired or partially fixed subproblem. For 357 events a valid full-feasible incumbent was available on the same date/horizon somewhere in the two panels. No lower bound exceeded the best such cost by more than 0.0001. One California 48-hour bound had no known upper bound for comparison. Cross-arm checks are retrospective and were never supplied to a competing solver. A comparison with an upper bound can detect an impossible inversion. Passing that comparison does not certify dual feasibility or branch-and-bound arithmetic. In particular the LP value is HiGHS' optimal objective with a scale-based downward adjustment of one part in ten million. Its safety margin is heuristic. Report any target as a solver-reported numerical gap to a validated feasible incumbent. Rigorous certification would require a separate validated global lower-bound proof. No such proof or dual certificate is archived for these UC instances.

Each record stores the remaining pre-interruption progress. A successful setSolution call, an acknowledgement in recovered_full.log, and a newly improved unrestricted incumbent are distinct observations. Transfer metadata is checkpointed on later solver events or stage completion. If a worker exits beforehand, absence of that metadata alone cannot exclude a submission. The audit checks surviving solver logs separately and cross-checks their reported start objective against the prep incumbent. A run that stopped before worker readiness provides no solver comparison.

From the W04 root, use a fresh output directory to reproduce the 48-cell attribution and numerical-bound review.

    python3 D/transfer_review.py --primary D/raw --serial D/serial_raw --out /tmp/w04-uc-transfer-review

The machine-readable cell evidence is in transfer_review/cell_attribution.csv. Aggregate results and cross-arm comparisons are in transfer_review/transfer_review.json. Canonical schedule feasibility and name-aligned objective replay are separately performed by D/check.py.
