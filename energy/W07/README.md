# CRGC W07 independent review packet

Start with [the results report](W07_Results.pdf) and [the independent-review assignment](W07_Independent_Review_Prompt.md). The [editable report](W07_Results.tex) compiles as a standalone article. The [44-claim ledger](claims.csv) links each conclusion to its evidence, assumptions and a falsifier. The W06 adjudications and W07 design are in [protocol](protocol/). The [unaltered 91-page v0.6 manuscript](manuscript/CRGC_Whitepaper_v0.6.pdf), [literal source](manuscript/CRGC_Whitepaper_v0.6.tex) and per-block checks are in manuscript/. This is a private research handoff.

## Reproduction

Use Python 3.12 and the versions in requirements.txt; environment metadata is in protocol/environment.json. From an extracted W07 directory create a fresh output directory outside that directory for each command. For numerical and finite checks, including a new A/E campaign, run:

    python -B reproduce.py /tmp/w07-numerical --fresh

For a fresh project Lean build with the matching pinned compiler and nine clean built dependency checkouts, pass their absolute paths in LEAN_BIN and PACKAGES:

    python -B reproduce.py /tmp/w07-lean --track B --lean "$LEAN_BIN" --packages "$PACKAGES"

The full default track validates the embedded SHA-256 manifest, reconstructs v0.6, checks stored A/B/E/C outputs, runs W06 regression checks and evaluates the longer UC schedule against upstream rows. With --fresh it also regenerates the numerical A/E holdouts, retraces the historical E case and compares economic outcomes. The archive verification receipt accompanies the ZIP externally, so it can report the hash of the ZIP itself. Re-execution can change timings, deadline-limited MILP incumbents and library log ordering. C/README.md documents how to rerun unrestricted solver searches. B/README.md gives details of the formal build and kernel replay. A new machine must supply the pinned external libraries and toolchains. Both TeX articles compile with pdfLaTeX (TeX Live with TikZ, Latin Modern and standard AMS packages); repeat three times in a scratch build directory for references.

## Evidence

- [W07-B](B/README.md) contains Lean, axiom inventories, deliberately false statements, exact controls, an explicit real-infimum qualification, primary literature and the A/E engineering correspondence.
- [W07-A](A/README.md) includes the pre-run lock, seed generator, original leaf weights and issued forecasts, native and exact comparators, timings, baseline audits, 15 compressed proofs, development attempts and historical regression.
- [W07-E](E/README.md) includes the pre-run freeze, 12 multi-day input panels, kernel, 192 certificates, trajectories, failed actions, historical one-call replay, small games, revaluation and separate calendar relaxation. A [second forward implementation](review_checks/E_scope.md) checks the information and economics independently of the simulation code.
- [W07-C](C/README.md) includes pinned PGLib source inputs and license texts, original objective witnesses and rigorous floors, registered timeouts and stronger post-run diagnostics. The longer unrestricted April UC solve and its exact verification are under C/postfreeze/direct_uc/.
- Each folder identifies exploratory work. Sources shared between implementations remain shared evidence. The separate receipt is an archive-external same-host execution record. Independent expert adjudication, field forecasts, operating costs, contractual service accreditation, and general solver rankings remain open.

For handoff to Chat, attach the complete ZIP and the external JSON receipt. Paste W07_Independent_Review_Prompt.md as the review request. The standalone report PDF may also be attached for convenient reading.
