# W04-A · Battery MIP starts

Use the W03 Python 3.12 numerical environment with the pinned packages in ../foundation/requirements.txt. The default foundation is ../foundation. Its source is imported read-only. The primary run and all archived datasets use a one-hour period. The mathematical objectives are synthetic cost units.

## Run

From this A directory on a Unix-like machine with the dependencies installed:

~~~sh
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
python campaign.py run --out /tmp/w04a-fresh
python analysis.py --out /tmp/w04a-fresh
python start_audit.py --out /tmp/w04a-fresh
~~~

Use a new directory for each full run. To recheck the delivered witnesses and recompute the summary in a working copy, pass its results directory to analysis.py and start_audit.py. campaign.py verifies the prospective code/input hashes before running. To regenerate candidate time-share development trials separately, use campaign.py prepare --out with an empty directory. The normal holdout command always loads the recorded decision in protocol/freeze.json.

The foundation can reproduce its W03 baseline with its own reproduce.py --experiments A --output command. legacy_replay.py takes the original and fresh W03 holdout JSONL gzip archives as positional arguments. Its optional --reviewer accepts the supplied v0.3 review evidence ZIP. Use --out for the destination JSON.

## Evidence layout

- protocol/plan.md, freeze.json, instances.json, development.json.gz contain the prospective protocol, selection decision and exact source hashes, all 72 frozen cases, and all 18 candidate-budget development trials.
- results/trials.jsonl.gz contains the original run. One object stores one case/arm/repeat, timestamped primal and dual events, powers from each improving incumbent and final solver return, raw feasibility residuals, stage timings and start-processing log excerpts. Physical power arrays use device then hour order. The LP primal can be returned by the solver and rejected by the device validator. Every reported snapshot marks only on-time events.
- results/trials.csv gives target, fixed-clock snapshots, normalized integral, wall time and process-level high-water RSS. On the study Mac the native RSS unit is bytes. Peak RSS is cumulative within a process, including previous trials, unsuitable for attribution to one formulation.
- results/stages.csv, start_audit.json document full original dimensions, restricted candidate status, solver-confirmed starts, transfer verification and status-specific counts. Diagnostic LP-infeasible fixed signs and physically invalid raw LP schedules are preserved. The solver may give an initial candidate the same cost as the supplied fallback.
- results/case_medians.csv, paired_case_differences.csv, contrasts.csv and target_counts.csv preserve the denominators and all paired differences. Smaller cost, area or capped time is better. Significance intervals are descriptive percentiles from resampling six day-independent seed labels across sizes within each cohort; the scheduling models here use constructed instances, not sampled operating days.
- results/exact_bounds.json holds a post-run rational certificate value for each case. Corresponding multipliers are carried by each repeat-zero full_lp trial. analysis.py reevaluates every dual component and every supplied power trajectory against the public model code.
- results/w03_replay.jsonl.gz and w03_reproduction.json contain the fresh W03 baseline replay and original/replayed fixed-clock checks against the reviewer package.

Positive MIP-start acknowledgement establishes numerical acceptance. The matched no-transfer arm is needed to compare resulting search trajectories. When a tested policy meets target at the full LP stage, no grouped model or subsequent MIP start is needed.

To reproduce the additional diagnostic tables after running the primary analysis, use the following commands. These scripts add descriptive stratification, transfer and perturbation checks. Their results do not select solver settings or change the frozen endpoint.

~~~sh
python supplement.py --out /tmp/w04a-fresh
python mechanisms.py --out /tmp/w04a-fresh
python mutation_checks.py --out /tmp/w04a-fresh/mutations.json
~~~

The use of the 3.5% terminal tolerance applies only to alternating seeds of ordinary and negative-outage cases. Forced-opposition and interchangeable cases retain exact individual endpoints. Per-case timing begins with unscaled numeric arrays already loaded and ends with checked actions and on-time bound events; JSON input deserialization and output archival run outside the numerical clock. Formulae, population and ranking rules are in protocol/plan.md. The supplied candidate time share is a ceiling on the entire prefix before unrestricted optimization. Equal solver settings and the same trained share apply to LP-repair and grouping.

Run `python presolve_check.py --out /tmp/w04a-fresh` to regenerate isolated presolve diagnostics on all 72 full LP, full MILP and single-shared-mode matrices. They time the standalone HiGHS presolve API with fresh solver objects and no initial incumbent. Integrated run timing is available only for the combined solve with callbacks. These diagnostic measurements must not be added to the main pipeline wall clocks. In a reduced-to-empty or infeasible presolve state, the returned reduced matrix can be empty; consult status alongside reductions.
