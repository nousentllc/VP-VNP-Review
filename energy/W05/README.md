# CRGC W05 experimental handoff

Read **W05_Results.pdf** for the nine-page results report, **claims.csv** for the evidence behind each claim, and **protocol/coverage.md** for the protocol, deviations and remaining proof or measurement obligations. **W05_Results.tex** is standalone editable LaTeX. The literal 17-block master export and its compiled 66-page PDF are in **manuscript/**. The freeze documents, development selections, failed tests, original raw data and separate post hoc studies are included.

## Contents

| Track | Start here | Raw and audit evidence |
| --- | --- | --- |
| B, feasible reconstruction | B/FINDINGS.md, B/LITERATURE.md, B/README.md | B/formal/, B/results/lean/, B/engineering/holdout.jsonl.gz and B/engineering/README.md |
| E, control | E/FINDINGS.md, E/EXPLORATORY.md | E/inputs/, E/results/primary.jsonl.gz, E/results/controlled_replay.jsonl.gz and E/results/analysis/ |
| A, screening | A/FINDINGS.md | A/protocol/, A/results/trials.jsonl.gz, A/results/small_exact_primal.json.gz |
| C, sparse AC models | C/FINDINGS.md, C/review_notes.md | C/inputs/, C/raw/, C/profile_raw/, C/analysis/, C/initial_review.json |
| Source and bibliography | manuscript/README.md, manuscript/bibliography_audit.md | protocol/source_pages.json.gz, manuscript/source_order.json, manuscript/bibliography_audit.csv |
| Execution environment | protocol/environment.json, requirements.txt, reproduce.py | protocol/page_source_lock.json, per-track freezes, SHA256SUMS.txt, protocol/replay_evidence/ |

## Reproduce from the ZIP

Extract the ZIP to a private workspace, keeping the two directories **W04** and **W05** next to each other under **Energy_Explorations**. Files under W04 are byte copies from the previously released evidence archive. All new research is in W05. Binary Python wheels, the Lean compiler, mathlib build objects and the LaTeX distribution are external dependencies. Package versions and source revisions are recorded. The paper identity audit includes private source metadata and the packet is intended for the specified review handoff.

From W05, verify the manifest with the platform's SHA-256 utility and reconstruct the two source exports. Use a fresh output directory for every run. One standard installation is:

    shasum -a 256 -c SHA256SUMS.txt
    python3 protocol/export_pages.py
    python3.12 -m venv /tmp/crgc-w05-venv
    /tmp/crgc-w05-venv/bin/python -m pip install -r requirements.txt
    /tmp/crgc-w05-venv/bin/python reproduce.py audit --out /tmp/crgc-w05-audit

The audit reads the original samples, repeats the witness checks and recomputes numerical tables. It checks frozen inputs before executing. It reconstructs the AC metrics from the original logged clocks and audits the exact output of the controlled E replay. To additionally rebuild the Lean sources, provide the actual matching Lean executable and the pinned mathlib package-checkout directory through the options --lean and --packages, or through W05_LEAN and W05_LEAN_PACKAGES. B/README.md explains how to obtain the pinned dependencies and interpret the seven expected compile failures. Keep Python assertions enabled.

With those environment variables set, these commands launch full clean verification or new experiments and write independent outputs:

    /tmp/crgc-w05-venv/bin/python reproduce.py audit --out /tmp/crgc-w05-audit-with-lean
    /tmp/crgc-w05-venv/bin/python reproduce.py rerun --out /tmp/crgc-w05-fresh

One can select a subset with --tracks B E, --tracks A, or --tracks C. For an explicit numerical-only fresh B run use --skip-lean. The full run recomputes the original and supplemental B experiments, E nominal policies and controlled replay, A trials and C timed solves and profiles. Fresh clocks and time-limited solutions can vary. The archived sole timing run, subsequent checks, and new output directories stay separate. Each invocation records individual commands' inputs by script, return codes, elapsed times, verification outcomes and logs. Track-specific READMEs and C/plan.md document the policy/model definitions. No network access is required for the evidence audit after installing dependencies.

To rebuild the report or master, from W05 use the following commands with pdfLaTeX available and an existing fresh output directory. Repeat the master build until its auxiliary files stabilize. The report has no external figures or bibliography database.

    pdflatex -no-shell-escape -halt-on-error -output-directory=/tmp/crgc-typeset W05_Results.tex
    pdflatex -no-shell-escape -halt-on-error -output-directory=/tmp/crgc-typeset manuscript/CRGC_Whitepaper_v0.4.tex

A bibliographic identity match, exact finite-case certificate, kernel-checked theorem and measured runtime make different claims. The ledger states their assumptions. The absence of operational forecast vintages, independent hardware timing and full industrial validation limits generalization. Engineering parameters and service valuations in these studies are synthetic.
