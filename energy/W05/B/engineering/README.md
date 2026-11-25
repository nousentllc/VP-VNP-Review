# Numerical AIPC experiment

Start with plan.md and freeze.json. The primary gate admits a schedule only if the proposed anchor is rationally feasible for the original fixed-mode model. Raw data, settings, matrix construction, multipliers and candidate points are in holdout.jsonl.gz or reconstructible from model.py and the recorded seeds. The family changes temporal profile, prices, margins or relative device directions. Integer modes are fixed by construction throughout. This is a continuous slice of a fleet, and is distinct from the unrestricted integer experiment in A.

analysis/certificates.csv contains full and reduced lower and feasible upper values, bound components, movement comparisons and timing. analysis/slots.csv distinguishes one-slot constructive feasibility, multi-slot recovery and unresolved trials. The synthetic dispatch cost omits common fixed import purchases, which affects the scale of relative thresholds. Interpret inequalities using exact fractions. The repair LP comparison uses the very same L1 movement budget as the segment gave itself.

analysis/primary_failures.csv logs the seven failed proposed anchors; the original exception text appears in holdout.jsonl.gz. amendment.md defines a follow-up on the same unchanged plants. See anchor_retry.jsonl.gz and the secondary group in analysis/summary.json. support_study.md and support_analysis.csv address the separate post hoc cost of tightening projection supports over the physical polytope. Each support maximum uses a validated unrestricted-within-mode dual upper certificate. Candidate-specific beta may change because a different reduced problem can return a different raw candidate.

Use the root reproduction driver (or run the following from this directory with the pinned Python packages). Write new results to fresh files in a new directory. The check-only support command writes its summary to the directory containing the support archive.

    python campaign.py run /tmp/w05-b/holdout.jsonl.gz
    python diagnose.py /tmp/w05-b/holdout.jsonl.gz /tmp/w05-b/retry.jsonl.gz
    python check.py /tmp/w05-b/holdout.jsonl.gz /tmp/w05-b/retry.jsonl.gz /tmp/w05-b/analysis
    python tighten.py /tmp/w05-b/holdout.jsonl.gz /tmp/w05-b/support.jsonl.gz
    python tighten.py /tmp/w05-b/holdout.jsonl.gz /tmp/w05-b/support.jsonl.gz --check

The finite tests in this directory evaluate candidate quality and strict feasibility for stored coefficients. The universal lemmas and their Lean replay are in the parent B directory. The sampled support, movement and anchor-acquisition timings describe one shared machine.
