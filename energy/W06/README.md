# CRGC W06 · Certified Opportunity Assessment

Start with **W06_Results.pdf** and its standalone editable **W06_Results.tex**. **claims.csv** links the findings to their local evidence, and **protocol/coverage.md** lists limits and unresolved obligations. All prices, operating states and outcomes are tied to the named models.

| Directory | Contents |
|---|---|
| B | Lean source, locks, theorem inventory, counterexamples, exact controls and kernel logs |
| A | Frozen deterministic storage cases, hierarchy, exact witnesses, direct optimization and timing comparisons |
| E | Historical W05 regression, chronological forecasts and actions, Bellman certificates, contracts and stronger policy comparisons |
| C | Licensed AC/UC inputs, checked AC existence, LP/commitment bounds, independent original-model checks and failed experiments |
| dependencies | Unmodified v0.5 source, frozen W05 experiment ZIP and subsequent independent opportunity review ZIP |
| protocol | Source identification, extraction of the W06 protocol, environment, comparisons and unresolved gates |

## Verify and reproduce

Python 3.12.9 was used on macOS arm64. The standard library is sufficient for integrity verification. Numerical audits require the packages in requirements.txt. The historical W05 regression and exact certificates run offline using files supplied in this packet. Lean and its pinned nine package checkouts/cache are external dependencies. The ordinary numerical audit skips Lean unless both Lean arguments are supplied. See B/README.md for the exact toolchain and the follow-up mathematical checks.

    python3 reproduce.py integrity
    python3.12 -m venv /tmp/crgc-w06-env
    /tmp/crgc-w06-env/bin/python -m pip install -r requirements.txt
    /tmp/crgc-w06-env/bin/python reproduce.py audit --out /tmp/crgc-w06-audit

Use a new output directory for each audit. Add --lean and --packages with the paths described in B/README.md to rebuild the primary and follow-up formal sources. The audit also verifies the strengthened one-hour reserve contract and depth-sensitive rainflow revaluation. Each track's README supplies fresh solver, policy or exact-control commands. Fresh clocks and deadline-limited candidate schedules may differ. To build the report, run pdfLaTeX twice on the standalone TeX file in a new directory. Per-file SHA-256 hashes are in SHA256SUMS.txt; the SHA-256 and extraction/audit record for the ZIP accompany it externally.

The registered experiments and their refinements are identified separately in the paper. Study A uses deterministic issued paths and an exact small discrete optimum. Study E uses common issued forecasts and a different chronological plant. Study C uses test-case objectives and its own relative threshold. Pooling frequencies across those contracts would change the research question.
