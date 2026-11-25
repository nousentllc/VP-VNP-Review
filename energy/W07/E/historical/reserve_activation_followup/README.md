# One-hour reserve calls and recovery

The primary study priced standby headroom. Its continuation rule would have violated inventory or accessible-energy limits in 137 of 1,655 tested upward calls and 133 of 1,629 downward calls. This post hoc study tests an expanded physical contract on the same 16 paths, after the independent challenge. All original results stay in their original paths.

An upward call substitutes q−u for the scheduled signed internal one-hour command; the opposite direction substitutes q+d. A voluntary extra upward block is offered only if the combined q−u−1 also works. These branches start from the pre-hour state and do not postulate an instantaneous reversal from the nominal schedule. Every branch must serve the same hourly demand under physical power, ramp, access, SOC and feeder limits. The branch can change SOC and the next hour's initial setpoint. The two-level safety calculation requires a causal terminal recovery for every one-call branch with subsequent deratings allowed and no further calls. The formula tests internal stored-energy blocks; the AC response of each block can vary with the sign and efficiency. Claims about fixed AC MW products, multiple calls, activation prices and operator dispatch require another model.

## Design and verification

For state x=(SOC, previous signed setpoint), K0(T) and K1(T) contain every state with SOC 9. At earlier times K0 requires, for each possible observed power derating, a nominal dispatch meeting the scheduling limits that lands in K0 at the next hour. K1 requires for each derating a nominal dispatch landing in K1 and, for each mandatory call direction, a legal separate activated edge reaching K0. An optional upward offer requires another legal activated edge reaching K0 and sharing the same pre-hour action. Future activations are excluded after the one call. The kernel is robust to all hourly power values 0, 1, 2 before the publicly clear last 16 hours, where power equals 2. Commodity price does not enter feasibility. The known demand envelope 1.8–4.8 MW makes both import bounds checkable at its extrema. Fresh path checks additionally used the exact observed hourly load.

The offline certificate minimizes the no-call path cost over this stronger contractual graph. An independent scalar implementation reconstructed both kernels, checked every edge of all retained integer cost certificates, recovered attaining paths, independently repriced each applied control, and explicitly tested every mandatory and offered call endpoint for physical feasibility and K0 membership.

| Mean per site-day, dollars | Seven days | Thirty days |
|---|---:|---:|
| Price rule minus offline optimum | 120.74 | 110.94 |
| Continuation minus offline optimum | 48.49 | 49.82 |
| Three-scenario MPC minus offline optimum | 48.63 | 47.04 |
| Continuation saving vs price rule | 72.25 | 61.12 |
| Continuation saving vs three-scenario MPC | 0.14 | −2.78 |

Eight of eight paths per horizon admitted full standby service and terminal recovery. None of the 16 seed/horizon contrasts beat the three-scenario controller by the $15/site-day practical target. All three causal policies served the published workload and maintained final nominal SOC. Each plan supported 1,655 upward and 1,629 downward mandatory hourly tests, and price/continuation/scenario supported 4,436/4,781/4,803 voluntary stacked upward tests. The experiment did not move the nominal trajectory after those separate tests. Across 21,312 realized decisions there were zero applied fallbacks and zero measured one-second deadline misses. The offline verifier checked 917,787 Bellman edge evaluations. Generation, kernels, offline certification, online dispatch and compressed output took 5.31 seconds. Independent verification took 0.33 seconds on this host. These safety and cost statements are conditional on the stated finite model and exogenous information. No new seed family was used, and no commercial ancillary revenue or multi-hour activation assurance follows.

## Reproduce

From this directory under the intact E tree, use Python 3.12.9 and NumPy 2.2.4. The relative E/inputs holdout files were locked by SHA-256. Use an empty scratch destination outside the released tree.

```sh
shasum -a 256 -c freeze.sha256
OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 python run.py --out /tmp/crgc-one-call
OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 python check.py --out /tmp/crgc-one-call
```

Read [frozen protocol](protocol.md), [per-path checks and decisions](results/audit.json), [inputs and pre-policy offline gate](results/gates.json), and [claims](claims.csv). Binary viability and cost potential arrays, with terminal row, are indexed in increasing SOC 2–11, then previous signed command −2 through 2. Online action fields are [nominal internal block, after-SOC, offered upward block, nominal stage cents, decision nanoseconds, fallback reason]. The one-call model is separate from all original contract outcomes.
