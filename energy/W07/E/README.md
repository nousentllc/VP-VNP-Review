# W07-E reserve activation, economics and recovery

Use Python 3.12.9 and NumPy 2.2.4. Code in this folder and W06 snapshots are project-authored. No commercial data, operational measurements or solver licenses are needed. Run from E with an empty output destination. Set OPENBLAS_NUM_THREADS=1 and PYTHONDONTWRITEBYTECODE=1. The incoming v0.6 protocol, W06 adjudications, common archive manifest and separate integrity receipt are at the wave level.

```sh
shasum -a 256 -c freeze.sha256
python regression.py /tmp/w07-e-review/historical
python run.py freeze /tmp/w07-e-review/fresh
cmp results/inputs.sha256 /tmp/w07-e-review/fresh/inputs.sha256
python run.py run /tmp/w07-e-review/fresh
python summarize.py /tmp/w07-e-review/fresh
python compare_replay.py results /tmp/w07-e-review/fresh /tmp/w07-e-review/replay-match.json
python calendar_relaxation/run.py /tmp/w07-e-review/fresh /tmp/w07-e-review/calendar
python calendar_relaxation/check.py /tmp/w07-e-review/fresh /tmp/w07-e-review/calendar
```

The primary freeze.sha256 predates holdout optimization and includes decision/statistics/checking code, all twelve seed files, W06 constructor and original inputs. The exploratory calendar check has its own separate freeze. Benchmarks use the complete finite models in PROTOCOL.md. The three-scenario baseline on fresh inputs is the released W06 common-first-action H12 planning rule applied to W07's own power, activation, reserve amounts, economic obligations and safety masks. Fixed W06 regressions retained the historical product and optional bids.

## Evidence map

- results/historical_regression/ contains the freshly rerun W06 audit, cost potentials, traces and independent two-down witness. Frozen independent W06 review rulings live at wave level.
- results/design.json, results/inputs.sha256 and results/inputs/ bind all economic and information fields. Each input includes exact chronological loads, prices, availability, booking arrivals and issued forecasts. Seed and planned calendar are never input features for action selection. The calendar is used only after nominal q to realize an activation.
- results/kernels.json.gz contains Boolean values [t][remaining][state] including the terminal row, and all nominal safety masks [t][power][remaining][state][q+2]. State index is (SOC-2)*5+previous+2. Every integer budget 0..4 is verified; budget 3 serves as a successor in the four-call game. Calendar time, declared public last 16h at full power, known hourly reserve direction, physical demand envelope and zero discretionary job shedding make other state dimensions redundant for this physical kernel.
- results/gates.json and results/certificates/ contain original-reference dollars and full Bellman potentials written before comparator evaluation. Values are integer cents. The sentinel 1,000,000,000,000 denotes infeasible. Each oracle sees its full calendar and exogenous sequence while all candidate actions pass the declared *universal* robust safety filter. All eligible robust policies project into this oracle; its decision-information advantage bounds possible gains.
- results/outcomes/ contains all 768 simulator outputs. Each completed step is [nominal q, call sign, applied a, ending stock, remaining K, energy cents, wear cents, signed standby transaction cents, signed activation transaction cents, forecast fallback flag]. An infeasible comparator stops immediately. Its attempted action and state are recorded under failed. A partial sum must never be compared to a full matched trajectory.
- results/activated_components.json.gz independently exposes gross imports, energy/wear/capacity/activation components, available/unavailable reserve, booked service and midnight pending jobs, actual vs nominal AC response, matched no-call recovery changes, closing credit and all three fixed-schedule rainflow sensitivity rates. Commodity-energy and activated response units are distinct. There is no extra fee that double counts the recovery cost difference.
- results/independent.json records independent scalar reconstruction of all viable actions, 1500 full starting-state game-tree checks, every integer oracle Bellman cell and all applied hourly outcomes. results/small_optimum.json reports the independently enumerated small causal optimum under each specified wear objective. Future activations on the 72-hour product are uncertain without a probabilistic policy-optimization guarantee.
- results/summary.json and claims.csv record 48 seed/calendar cells per budget, and the bootstrap/sign convention: three-scenario cost minus single-scenario cost. Seeds alone supply independent clusters. No-call calendar copies for K=0 carry weight, not statistical independence.
- calendar_relaxation/ is a separately frozen, post-primary investigation. It permits knowledge of exogenous paths while retaining shared actions at indistinguishable realized call histories. The independent checker rebuilds every partition and compares sum-weighted Bellman potentials to both endpoints.
- results/timing.json, results/cold_wall.log and the regression/extension logs contain host timings. The host time utility printed a harmless permission warning when querying CPU clock metadata after returning wall/user/system times. The fresh run reports its own peak process memory. Python precomputes all state-indexed feedback decisions from each currently issued forecast for replay efficiency. The table-construction clock charges for this work; aggregate timings do not measure a field actuation deadline.

The historical activation bound and curves are conditional on synthetic bookings, prices, derating and an announced clear terminal window. This campaign provides no evidence for fixed-grid-MW delivery products, sustained multi-hour commands, weather-dependent commercial call rates, lifetime estimation, outage accreditation or site revenue. Rainflow uses the published illustrative curve in [Xu et al.](https://arxiv.org/abs/1707.04567) with whole-path half cycles as in [Shi et al.](https://arxiv.org/abs/1703.07968). Zero unserved service on completed paths is a hard constraint. Independent review should vary availability/terminal promises before transferring figures to a different contract.

A post-primary audit independently rebuilt every nominated H12 action, including both failed comparators, from the current issued observations only. Run python policy_audit.py results /tmp/w07-policy.json. It also verifies actual job booking due times and cross-midnight continuity. For an independent full run made with the commands above, python compare_replay.py results /tmp/w07-e-review/fresh /tmp/w07-replay-match.json compares every deterministic result file and the timing-independent checker counts.
