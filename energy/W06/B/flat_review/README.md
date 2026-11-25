# Exact economic saturation on the W05 flat tariff

This is a post hoc cross-track result prompted by W06-E's historical diagnostic. The mathematical argument applies to a declared flat import price p, an AC throughput cost w on each charge or discharge MWh, a final stored-energy credit v, a constant positive charging coefficient e, and a fixed draw ratio b. Competitors must meet the same hourly service profile and retain the true grid import cap, ramp history, operational restrictions, energy dynamics and applicable final-stock contract. The lower certificate may omit restrictions that only tighten the candidate set. Every baseline must still be feasible.

For total served energy Y, aggregate AC charging C and discharge D, the balances are imported energy Y+C−D and final stock S=S0+eC−bD. Substitution into p(Y+C−D)+w(C+D)−vS gives

    J = pY − vS0 + ks(S−S0) + kd D
    ks = (p+w)/e − v
    kd = (p+w)b/e + w − p

The stored binary64 coefficients encode e=0.94 and b as the binary64 evaluation of 1/0.93. The checker uses their exact dyadic representations, preserving the W05 coefficient convention. With p=50, w=10 and v=50, ks≈13.829787 USD per stored MWh and kd≈28.634180 USD per discharged AC MWh. Sufficient sign conditions are 0<e≤1≤b, p,w≥0 and ve≤p+w.

An initial valid grid envelope is min(grid-cap, hourly served energy + available charging power) in 1-hour intervals. Forward and backward propagation enforce ramp limits while preserving an upper bound on every feasible import trajectory. A lower bound on total discharge is the sum of the positive parts of service less that envelope. A competitor may also face charging power, discharge power, SOC, reserve or exclusivity constraints. These do not expand its allowable trajectories. The exact analytical savings cap at a terminal floor F is

    ks (S_baseline − F) + kd (D_baseline − D_min).

With equal closing stock, kd≥0 is sufficient; ks may have either sign. Fill attains D_min in all 252 historical cases and all 12 continuous fill splices. The alternative can at best equal its matched-stock flat-tariff cost. The floor-only cap retains the terminal term and does not certify that the floor is economically or physically attainable. These splices reuse W05 days. Their contribution is mechanistic, without independent out-of-sample evidence. Hourly changing prices can assign different costs to schedules with equal total discharge and closing stock. The W06 variable-price control model requires a separate analysis.

## Checks and artifacts

[FlatTariff.lean](FlatTariff.lean) proves the two envelope passes, the per-hour cap, aggregation of forced discharges, tariff identity/signs and scoped savings bounds. The three counterexamples preserve the dependence on the terminal-credit sign, discharge coefficient and flat tariff. [FlatAudit.log](logs/FlatAudit.log) records the statements and axioms. [FlatMutants.log](logs/FlatMutants.log) records the three expected rejections. [Audit](logs/audit.json) records exits and transitive axioms. The distributed Lean kernel replays the positive module; the pinned imports are those of the core.

The independent finite checker reconstructs fill in exact arithmetic and checks every primitive feasibility row, compares every original hourly output against the archived W05 witness, and checks the cost decomposition on each path. Its envelope uses all time-pair distances from import caps and the initial import value. The triangle inequality for ramps makes each pairwise expression a valid upper bound. This implementation neither calls the E forward/back sweep nor uses LP multipliers. It compares its results with the E records. [Per-path exact values](data_check.json.gz) contain source hashes, coefficients and the 264 original-or-spliced path outputs. [Input provenance](inputs/source_lock.json) traces the two bundled original W05 members to the frozen parent archive. Numerical data and assumptions are shared with E.

From the W06 campaign directory, run the commands below with the core proof environment or use Python alone for the data checks. Use fresh output locations.

    python3 B/flat_review/verify_flat.py --lean "$LEAN_BIN" --packages "$PACKAGES" --out /tmp/crgc-w06-flat-proof
    python3 B/flat_review/check_data.py --out /tmp/crgc-w06-flat-data.json.gz

Passing --w05-zip with the original W05 ZIP adds a read-back comparison of both source members. The pure Python driver uses the frozen source members and E/historical by default. Machine checks of the abstract Lean inequalities and the Python data reconstruction are two distinct trust steps. A formal equivalence between operational software and the mathematical model remains open.
