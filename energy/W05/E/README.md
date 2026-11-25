# W05-E control-policy comparison

Use the frozen W04 Python environment and run these commands from W05. W04 is a sibling of W05. An extracted W04 foundation can instead be supplied with W05_W04_ROOT. The protocol/freeze.json SHA-256 map checks the specific dependencies used. Python numerical package versions and rule/comparator selection are in that file. Set PYTHONDONTWRITEBYTECODE=1 when working inside the release tree.

    python E/run.py --out /tmp/w05-primary.jsonl.gz
    python E/run.py --out /tmp/w05-controlled.jsonl.gz --signals-from /tmp/w05-primary.jsonl.gz
    python E/audit.py --primary /tmp/w05-primary.jsonl.gz --repeat /tmp/w05-controlled.jsonl.gz --out /tmp/w05-e-analysis
    python E/diagnostics.py --out /tmp/w05-e-analysis

To independently recompute all numerical/physical summary tables from recorded actions, replace the two raw arguments with E/results/primary.jsonl.gz and E/results/controlled_replay.jsonl.gz. The audit only needs Python and NumPy. The diagnostic script creates the Pareto and nested-control tables after metrics exist. The original solver rerun uses one thread per HiGHS instance with dual/primal tolerance 1e-8. Implementation-wide unit checks use a 1e-6 threshold. A new live run may have different clocks. The controlled replay feeds a complete fresh copy of the model and input to each policy with the prior observed timeout branch fixed. This reproduces simulated decision semantics given those deadline signals. No physical process is attached.

## Data dictionary

The main issue generator is the pinned W03 implementation imported by W04. Alternative data come from the separately specified synthetic process in design.py. At each local date hour, load[0] of the issued packet equals its contemporary observation. The independent generator is a model-form sensitivity implemented by the same research group. Each case contains 24 actual loads, public reserve/floor calendars, actual battery availability and 24 issue-time forecast records. All intervals are one hour, powers are MW, and energy balances are MWh.

Each raw JSONL row holds one scenario/arm, with ordered hourly [grid MW, charge MW, discharge MW, flexible unserved MW, end SOC MWh] actions. Per-decision metadata records forecast eligibility and actual prefix used, terminal target and model calls, sequential LP objective values, one-step fallback readiness, measured candidate time and late/error reason. “Info” is the number of exposed forecast entries, not a promise of policy optimality at those inputs. The offline reference receives the full realized day before decisions. The synchronous gate selects fallback when the measured decision clock exceeds one second; online communication and physical actuation are outside this test. Reserve headroom lost during a battery outage remains a recorded service exposure, even when the selected action passes the simulated dispatch constraints.

Names ending in 3/6/12 indicate maximum forecast horizon. Policies whose names begin with w04 use the earlier precautionary target. For example w046 denotes W04 target @ H6. Learned3/6/12 use the W05 development-fitted conditional target. Rule3/6/12 refer to rule variants chosen on W04 at each horizon. Legacyrule6/12 apply W04's earlier original rule. Adaptive and fixed12 pay for both H6 and H12 optimizations, with fixed12 always using H12. Nested6 takes the learned H6 action after dropping the H12 tail, and nestedrule6 does the same for the chosen H6 rule. Flat12 substitutes lead 5's load for the six longer entries in a twelve-hour optimization.

For development-only reconstruction, in a disposable package copy run E/design.py develop, then E/design.py freeze. Compare generated inputs and calibration with their SHA-256 pins. Stage objective floating-point values, native-wall snapshots, the freeze timestamp, and platform strings can vary across environments. Existing files in the original record should be preserved. Recomputing the primary or signal replay requires fresh raw output filenames. All numerical estimates are model conditional; the independent generator and main panel retain separate denominators.

## Independent full-information opportunity certificate

The optional retrospective computation and its solver-free checker can be run after the primary record. The verifier requires only Python and the shipped inputs/witnesses.

    python E/opportunity.py --primary E/results/primary.jsonl.gz --out /tmp/w05-opportunity
    python E/verify_bounds.py --certificates E/results/analysis/opportunity_certificates.json.gz --out /tmp/w05-bounds-verified.json

For a new raw run use its --primary JSONL path in the first command. EXPLORATORY.md derives the bound, the exact arithmetic convention, the primal/dual relationship and the limitation to the realized full-information sample.

Use the following additional solver-free check for exact agreement between nominal and logged baseline shedding/terminal stock and the uniform residual sensitivity.

    python E/baseline_alignment.py --raw E/results/primary.jsonl.gz --certificates E/results/analysis/opportunity_certificates.json.gz --out /tmp/w05-baseline-alignment.json
