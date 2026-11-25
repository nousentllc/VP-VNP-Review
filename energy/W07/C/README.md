# Static AC and conventional unit commitment

The registered inputs are the six public source files in sources.json. They define eight operating problems because each of the two UC dates is evaluated at 24 and 48 hours. See freeze.json for the pre-outcome contract, code hashes, weights, spending limits and eligibility. The licenses and published UC mathematical model are in inputs/. cases.csv records exact rational endpoints. Each original solver job, including the two failed clique transports, has a process-clock receipt and raw log in logs/.

Run with the root requirements and one BLAS/OMP thread. From C, run python -B check_lock.py. For the delivered certificates, independent row and full-box checks and embedded W06 regression, run:

    python -B verify.py /tmp/new-w07-c-audit --w06

For fresh deadline-dependent solver searches use:

    python -B run_campaign.py solve ac /tmp/new-w07-c
    python -B run_campaign.py solve uc /tmp/new-w07-c

Use empty output paths. Commands launch case-specific subprocesses, record exit codes and continue on failed tiers. Check each receipt. Upper witnesses and timings can vary. The registered check operations operate on the supplied output directory. A missing stronger-tier certificate remains missing.

Both 162-bus registered clique jobs failed when a dual vector was unavailable. Keep their primary lower bounds. clique_diagnostic.py repeats the same method and retains the verified prefix and solver termination state. It reports a separate wall clock. The supplemental coverage.py, tree_coverage.py and feasible_gains.py implement post-freeze checks of the declared original-feasible-set, exhaustive split and feasible-gain tests. They had no influence on case selection or registered searches. The name exploratory/ was inherited from W06. W07 predeclared these particular escalation rules in freeze.json. Further investigations are stored under postfreeze/.

The regression ZIP contains the byte-unchanged subset of W06 required by the historical checks. W06 carries zero fresh weight. Each public input's blob and commit can be independently checked against the original publisher. The report links the formulation and relaxation precedents.

The April 48-hour follow-up has its own pre-run registration in postfreeze/direct_uc/. It tests 120 seconds of direct optimization, using the same model, seed and 30-second reference schedule, after that case remained open. Run direct_followup.py check and audit_direct_original.py to independently verify the new rational candidate and objective. To regenerate its deadline-limited solve use a disposable working copy with an empty postfreeze/direct_uc/summary.json location (the code refuses to overwrite the archived study). The original solve and registered classification stay in uc_results/.
