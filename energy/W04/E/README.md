# W04-E reproducibility

From the W04 directory use the pinned W03 Python environment in foundation/requirements.txt. Set PYTHONDONTWRITEBYTECODE=1 to keep the packet clean. The shipped holdout and training fit are sufficient for offline replay. Use a new output path for each numerical run.

    python E/campaign.py run --out replay/E_first.jsonl.gz
    python E/capture_replay.py --out replay/E_second.jsonl.gz --plans replay/E_projected.jsonl.gz
    python E/analyze.py --raw replay/E_first.jsonl.gz --repeat replay/E_second.jsonl.gz --out replay/E_summary

For a complete audit of the shipped trajectories and projected plans, run the following from W04. The destination must be new and outside the archive. The audit checks both panels, recomputes the full first- and second-pass comparisons, and also writes projected-tail feasibility, observed clock attribution, fallback-free paired sensitivity, loss/throughput Pareto counts and tail forecast errors. Its source-file digests are captured in audit_inputs.json. New timing measurements from forced-clock and fallback reconstruction can differ on every run.

    python E/supplemental_audit.py --primary E/results/holdout.jsonl.gz --repeat E/results/repeat.jsonl.gz --plans E/results/projected_plans.jsonl.gz --out /tmp/crgc-e-supplemental-audit

To check a fresh pair of runs, pass their two action files and the second pass's corresponding plan file to the same command.

The independent accounting script requires NumPy and recomputes every power and energy constraint without invoking the optimizer. To check the original W03 comparison in a disposable copy of the packet, run the following. The development command regenerates the panel and calibration. The review command reproduces the single-action Linux substitution and the two-algorithm tie-break diagnostic.

    python E/campaign.py develop
    python E/review_case.py

## Raw data

Each row of the gzipped JSON lines contains one complete 24-hour simulation. Hourly action columns are grid import MW, charge MW, discharge MW, unserved flexible load MW, and ending SOC MWh. All intervals last one hour. Decision logs contain the actual issue hour, horizon, terminal target, sequential LP objective values, readied decision latency, and fallback reason. Offline solve time is recorded separately from action checks. The short-horizon policy input is a prefix of the stored maximum-horizon issue. Physical availability is revealed at the current and following hour. After that it is forecast available.

Policy names combine the variant and horizon. The rule is the original forecast-aware threshold. None and value use common deterministic service/throughput priorities and action tie-breaking. Value introduces soft target shortfall between service and throughput. Legacy6 retains both original W03 LP objectives with the solver's basis selection. Offline has perfect actual load and availability. Value12_tail6 holds the sixth load forecast flat through its tail.

The shared-forecast data contain one issue object per simulated hour. The synthetic workload generator, original W03 matrix builder, numeric packages, and archived original comparison are preserved under foundation/. Regime totals and per-seed effects stand alone as CSV files. The capacity reservation metric integrates unavailable committed power over time. Its units do not represent unserved computing demand.

## Review lineage and interpretation

inputs/reviewer_864.json contains only the material-discrepancy summary, environment and corresponding Linux trajectory from the supplied v0.3 reviewer archive's audit_w03.json. Its archived results are independent review evidence. The W04 simulations and new replays are internal. No independent W04 operating-system or utility replay is claimed. The three regimes per latent seed share the underlying day, so confidence intervals resample 24 clusters. The study evaluates deterministic controllers on stochastic synthetic days. It does not solve a multistage stochastic program.

## Verifying projected trajectories

The first holdout pass records realized actions, stage optima and decision timing. The second records the projected optimizer trajectories as well, including unapplied future choices, plus the matching rule's conditional recharge target. The observer receives each solve's return value and writes plans after a day-policy simulation. Run the bundled checker against the delivered second-pass paths from W04. Its output gives constraint checks and soft terminal-target misses.

    python E/analyze.py --raw E/results/repeat.jsonl.gz --out E/results/repeat_summary
    python E/replay_deadlines.py
    python E/deadline_sensitivity.py
    python E/check_plans.py
    python E/pareto.py
    python E/tail_accuracy.py
    python E/format_findings.py
    python E/write_ledger.py

Two replays can have different timings while taking exactly the same actions. The captured forecasts and rule targets are forecasts in effect when the action was taken. The README's replay/ example deliberately writes new raw and analysis paths. To audit a new run's projected trajectories with check_plans.py, use a disposable copy and put its second JSONL at E/results/repeat.jsonl.gz and plan JSONL at E/results/projected_plans.jsonl.gz.

Deadline attribution repeats each trajectory whose realized actions differed across the two live passes. It feeds the first pass's observed elapsed durations to the one-second decision branch, retaining all solver operations. The primary and live-repeat summaries always use actual wall clocks.
