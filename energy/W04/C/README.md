# W04-C replication

From the W04 root, set the single-threaded environment in the main README and use Python with foundation/requirements.txt installed.

    python C/opf.py run /tmp/crgc-c-fresh/raw
    python C/check.py /tmp/crgc-c-fresh/raw /tmp/crgc-c-fresh/analysis
    python C/analyze.py /tmp/crgc-c-fresh/analysis

For the delivered trials, use C/raw as the first checker argument and a new destination for analysis. The .npz arrays store CSC Jacobian/Hessian row indices and pointers plus the RCM permutation for each completed first-repeat structural probe. The json files store trajectories as four vectors (voltage magnitude, bus angle, active generation, reactive generation), feasibility residuals, times and solver status. Search elapsed includes data parsing, the DC start, expression and derivative construction, solve, full engineering reconstruction and audit. Process import, recording and post-clock surrogate diagnostics are outside this timer. The method's real-time applicability would require counting deployment-specific startup and communication too. The 110-second external guard covers both the timed run and post-clock diagnostics. If the guard fires before the single record is flushed, the status has no recoverable checked witness. An empty objective/condition or timing cell denotes missing evidence. See the exact table headings for conditioning on feasibility and deadlines.

W03 reproduction uses the original frozen source with W03_RESULTS pointed at a fresh destination. W04 degree counts incident active branch entries, so parallel lines count separately. The matched full starting generator guess can lie outside the box; IPOPT can push starting points within bounds. Conditional speed ratios are computed only for the same repeat with two on-time validated solutions and relative cost agreement at 1e-5. Missing pairs and all deadline misses remain in the primary attainment table.
