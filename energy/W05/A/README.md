# W05-A certified relaxation screen

The input panel, development outcomes, pre-run settings and scored code hashes are in protocol/. Run from W05 with the W04 packet as its sibling under Energy_Explorations. The dependency location used by engine.py is ../W04/foundation from W05. Use Python 3.12.9 with the exact numeric versions in that foundation's requirements.txt. The runner imports its model read-only. A new destination for each run protects the raw logs.

    export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
    python A/campaign.py run --out /tmp/crgc-w05a-new
    python A/analyze.py --raw /tmp/crgc-w05a-new/trials.jsonl.gz --out /tmp/crgc-w05a-audit
    python A/mechanism.py --raw /tmp/crgc-w05a-new/trials.jsonl.gz --out /tmp/crgc-w05a-audit

To replay the recorded witnesses, specify A/results/trials.jsonl.gz with a new --out for the last two commands. Development can be exercised in isolation with python A/campaign.py prepare --out /tmp/crgc-w05a-dev. The accepted results summarize only the original pre-frozen settings. Development ranking depends partly on host time. Candidate arms used identical information and rotations, subject to contemporaneous host load.

The primary native_cert arm starts with an unrestricted MILP and reserves an explicit interval for a rational LP certificate. The extra arm named native_unmetered_certificate gives the native MIP the full 2 seconds and computes no online exact lower certificate. Its independently certified target column is consequently structurally unavailable and counts as a miss under the blind rule. Report its native numerical and post hoc common-bound outcomes separately. The name reflects that the numerical native arm has no external certificate operation in its budget. Comparing only certified counts to this diagnostic would favor the certified procedures by construction.

Each raw JSONL row contains full native solver logs for all attempted stages, CPU settings, validation times, beginning and ending stage times, LP multipliers, exact rational bounds and primal power witnesses. Events include only on-time validated improvements or verified lower bound changes. End-of-solve witnesses can arrive too late, and physical checks may reject fractional LP schedules. Every lower certificate solves the same unrestricted continuous LP model, in an arm that budgets time for that operation. The post hoc independent checker uses separate physical and rational coefficient calculations to recompute event classifications. LP screening shares its successful exit with the strong LP-repair arm. Fixed sign and partial sign repair can fail even when a feasible full model exists. No grouped binaries are present.

Case medians use only complete triples for the relevant endpoint. Paired contrast rows include denominators, missing pairs, effect intervals and practical win/tie/loss counts. For U, first action, gap time or area smaller is better. The hit-rate contrasts compare screen minus baseline. Normalized area starts from fallback cost for integration only; fallback availability and physical validation latency are logged separately. An absent fallback, missing certificate, and near-zero fallback-to-bound range have explicit reasons in trials.csv. Per-arm raw traces permit alternative handling of coverage.

The practical tolerance for physical actions is 2e-6, in the relevant native constraint units. Bound claims apply exactly to binary64 input coefficient values interpreted as rationals, including the reciprocal efficiencies in matrix assembly. No exact rational primal lift for every numerically admissible schedule or uncertainty certificate for real battery parameters is claimed. The panel uses designed stress families and four seed clusters. It supplies neither prevalence estimates nor plant timing guarantees.

The exploratory fixed-mode rational vertex audit requires SymPy 1.14.0. Repeat it using the archived raw file or a new complete run:

    python A/rational_primal.py --raw A/results/trials.jsonl.gz --out /tmp/crgc-w05a-exact

See exact_primal_design.md for its predeclared subset within the post-freeze audit. Its exact stored-coefficient primal witness and gap are separate from timed primary scores.

The original frozen audit.py first completed primal, dual, and trajectory replay. Its CSV record omitted fallback_cost, causing a KeyError when computing the already specified practical U threshold. analyze.py adds that one missing field to the generated record. The frozen code, original exception and every raw trial are preserved. Use analyze.py for the completed audit.

Regenerate the human-readable track results and six claim entries from all checked tables in a new directory:

    python A/write_report.py --out /tmp/crgc-w05a-report --results A/results
