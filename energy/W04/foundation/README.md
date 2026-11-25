# Energy explorations · W03

**Start with [the results report](REPORT.md).** The editable report, [compiled PDF](W03_Results.pdf), [standalone LaTeX](W03_Results.tex), five experiments, fixed inputs, rejected schedules, published benchmarks, formal proofs and replay code are in this directory. The branch is private. The original CRGC manuscripts are maintained separately. [Energy research branch](https://github.com/nousentllc/VP-VNP-Review/tree/energy-explorations/energy/W03)

## Check the recorded packet

From an extracted copy of the packet, change to the W03 directory. SHA-256 verification covers the published files including the protocol, schedules, proofs and report. On Linux, use the corresponding sha256sum -c command.

```sh
shasum -a 256 -c SHA256SUMS.txt
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python src/verify_recorded.py
```

The read-only verifier reconstructs the battery lower bounds in exact arithmetic, rechecks archived schedules and compares AC objective values to PGLib’s published precision. It rebuilds and checks six unit-commitment schedules against the reference model. The two runs with no incumbent remain recorded failures. It recomputes battery losses, useful service and state-of-charge trajectories for all 72 site-policy runs. It reads the archived Lean log. Rebuilding the proofs is a separate command below.

## Reproduce the numerical experiments

```sh
python reproduce.py --experiments A C D E --output replay/numerical
```

Each experiment can also run alone. Supply a fresh output directory for each invocation. The normal A replay uses the development-selected presolve setting pinned before the holdout. Add `--retune` to repeat the development timing contest. The shipped inputs are sufficient for offline numerical replay once dependencies are installed. Numerical schedules may differ between optimal solutions, and machine speed, solver callbacks and deadlines can change a run’s outcome. Compare physical feasibility, cost, bounds and deadline success before comparing elapsed time. The controls rotate the battery method order and keep the seeds fixed.

## Rebuild the proofs

Install the Lean toolchain named in `formal/lean-toolchain` with elan. The package lock pins mathlib and its transitive dependencies. With network access for an initial setup, run the following from the W03 directory.

```sh
(cd formal && lake exe cache get)
python reproduce.py --experiments B --output replay/proofs
```

For an existing compiled package directory at the pinned revision, pass its location using `--lean-packages`. If several versions of Lean are installed, `--lean` accepts the path to the matching executable. The actual study compiled against a matching, read-only local mathlib cache. The repository includes the verified proof source, lock and logs. Dependency build products are supplied by the Lean/mathlib toolchain.

To execute the whole register in order, use `python reproduce.py --output replay/all` after installing the Python and Lean dependencies. A complete run also regenerates cohort tables and paired summaries. The archived clean replay is supplied in [the second-run archive](results/replay_raw.zip). To compare another complete replay with the primary run, use `python src/compare_replays.py replay/all`. [Observed run-to-run differences](results/reproduction.json) are recorded by case and policy. The primary run and its design history are identified in [the protocol](protocol/design.json). Machine-level execution details appear in [the freeze](protocol/freeze.json).

## Evidence files

| Location | Contents and interpretation |
|---|---|
| protocol/ | Prospective design, hardware, input hashes, selected tuning and implementation hashes at the recorded evaluation stages |
| inputs/ | Frozen synthetic cases and issue-time forecasts, unchanged public data and license notices, original W-E05 code and extracted historical metrics |
| results/A/holdout.jsonl.gz | One JSON object per case, policy and repeat. Events are timestamped upper or lower bound updates. Steps include stage status, reconstruction and solver-return validity. Powers are included on repeat zero. |
| results/A/ | Cohort and stage CSVs, development runs, paired uncertainty, separate presolve diagnostics and 24 exact box lower bounds |
| formal/ and results/B/ | Lean source and lock, executable exact controls, mutation results and the full axiom log |
| results/C/ | Case-specific costs, clock times, numerical lower bounds, independent validation, voltages, angles and generator injections |
| results/D/ | Per-arm chronological bound traces, solver status, model dimensions and validated schedules. NPZ files contain named Pyomo primal variables and values. Load with allow_pickle=False. |
| results/E/ | Day and policy traces. Hourly action columns are grid, charge, discharge, unserved load and ending SOC, in MW or MWh for a one-hour interval. Includes historical replay and paired regime totals. |
| results/quality.json | Rechecks of the delivered evidence. The two UC runs without a validated incumbent are explicitly counted. |
| claims.csv and sources.md | Claim scope, falsifiers, evidence paths, source provenance and reuse terms |

The integration key for this packet is W03 plus campaign and claim number. Existing v0.2 and v0.2.1 claim IDs remain version-specific. All solver policies are research simulations. No private Library files, Drive listings, field telemetry or earlier manuscripts are required for replay.
