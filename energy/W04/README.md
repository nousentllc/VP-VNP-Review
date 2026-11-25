# CRGC W04 experimental results

Start with W04_Results.pdf. W04_Results.tex is the complete standalone editable source. The root claims.csv maps conclusions and falsifiers to primary records. The supplied master was used as a version checkpoint. This archive is the separate research handoff.

## Verify or replay

From the extracted W04 directory, Python 3.12 can verify every archived file digest using only the standard library.

    python3 reproduce.py integrity

For numerical replay, create a Python 3.12.9 environment and install the shipped research dependencies. The research run used arm64 macOS. Runtime-dependent results require identical gates and are sensitive to host contention.

    python3.12 -m venv /tmp/crgc-w04-env
    /tmp/crgc-w04-env/bin/python -m pip install -r foundation/requirements.txt
    /tmp/crgc-w04-env/bin/python reproduce.py audit --output /tmp/crgc-w04-audit --exact-only
    /tmp/crgc-w04-env/bin/python reproduce.py rerun --output /tmp/crgc-w04-run --exact-only

For a full Lean source reconstruction, follow B/README.md to prepare the pinned compiler and package checkout/cache. Supply the executable path using --lean and the package directory using --packages in place of --exact-only. The exact-only flag affects just B. The audit path recomputes numerical evidence from stored dispatches and events. The rerun path executes the frozen policies again. Both paths take a new directory outside this archive. Limit scope with --tracks A,C or any other comma-separated subset. Fresh jobs run in sequence by track. The recorded run overlapped tracks and host load was not controlled. Replays may change deadline scores even with the same numerical dependencies. C and D may take many minutes. A fresh E replay preserves the projected plans as well as actions. The independent analysis and direct worker commands for one track are also available in its own README.

Compile the standalone report with pdfLaTeX in a new directory. The delivered PDF was built with pdfLaTeX. It has no external figure or bibliography dependencies.

    pdflatex -interaction=nonstopmode -halt-on-error -output-directory=/tmp W04_Results.tex
    pdflatex -interaction=nonstopmode -halt-on-error -output-directory=/tmp W04_Results.tex

## Evidence index

| Folder | Evidence |
| --- | --- |
| protocol | Supplied experimental contract, file hashes, environment, load observations, reviewer W03 evidence, data provenance and execution deviations |
| foundation | Byte-matched W03 source, data, public licenses, proof lock and original numerical records. Its SHA256SUMS.txt is the historical manifest |
| A | Frozen 72 device fleets, 1,080 trial traces, timed candidate and bound events, individual power witnesses, MIP starts, exact LP box certificates, W03 regression and candidate-budget development |
| B | Lean sources, theorem signatures, axiom inspections, mutations, exact controls, sharpness witness, compilation logs and dependency locks |
| E | Shared issued forecasts, calibration, primary and second-pass 24-hour trajectories, first actions, planned tails, clock failures and paired 24-day effects |
| C | Original public case files, 160 trial records, reconstructed AC points where available, structural derivative patterns, initialization audit, on-time comparisons and W03 regression |
| D | 24 primary worker attempts, native solver traces and commitment vectors when available, 24-attempt serial sensitivity, development errors and separately scored numerical bounds |

## Inputs and attribution

PGLib-OPF and PGLib-UC retain their original notices in foundation/inputs/ac/LICENSE and foundation/inputs/uc/LICENSE. Exact releases are recorded in protocol/environment.json. C/inputs retains typical and active-power-increase MATPOWER cases. D/inputs retains original JSON data locally renamed for stable lookup. Horizon truncation happens in memory. The PGLib AC local benchmark costs in foundation/inputs/ac/BASELINE.md come from a separate PowerModels.jl/IPOPT implementation with different timing conventions. See foundation/sources.md for the original W03 registrations and licenses. A/E simulated operations, W04 results and all clocks are internal research. The independently supplied Linux replay in protocol/review concerns W03. Review of the new packet remains the next independent evidence stage.
