# VP–VNP research review

The published statements faithfully express the exact nonuniform arithmetic-circuit separation, and the five released declarations passed the independent Lean and nanoda checks. Edition 12 closes this review at fifteen passes. The three short entry points are:

1. [Two-page verdict](report/verdict/VP_VNP_Verdict.pdf) — source custody, statement correspondence, kernel acceptance and the consequence of each discrepancy. [Editable verdict TeX](report/verdict/VP_VNP_Verdict.tex)
2. [Errata note for the publisher](passes/publisher-errata.md) — two proposed wording changes and two bounds already distinguished in the paper.
3. [Whole-chain companion](passes/14e-circuit-to-contradiction.md) — follow an arbitrary hypothetical small circuit through either field branch to the contradiction.

The [claim register](report/proof-coverage.csv), [66-page technical report](report/VP_VNP_Research_Review.pdf), [editable master](report/VP_VNP_Research_Review.tex) and [handoff for Chat](VP_VNP_Chat_Handoff.md) contain the derivations and verification boundaries. The [statement audit](passes/statement-correspondence.md) explains the exact and border models. The [response to external review](reconciliation/edition12-external-review.md) records the points on which the archived evidence qualified the reviewer’s reading.

## A reader's route through the argument

1. Fix a field, a matrix size and a hypothetical circuit. Earlier gates may be reused, constants may depend on the field and size, and cancellations are allowed. M.1 specializes all coefficients together to a comparison field. Read the HC and permanent projections to see why their characteristic restrictions differ. [Model](primary/vp-vnp/Statement.lean#L23) · [Theorem 1.1](primary/vp-vnp/paper.pdf#page=2) · [HC](passes/12b-hamiltonian-projection.md) · [Permanent](passes/pass13C-permanent.md)
2. In the flat branch, E.4 charges each reused gate once per balanced subset. E.7 permits differently cut summands. E.8–E.9 supply one spectral witness for all possible paying cuts. E.10 states log₂L≥ℓk√k/16. Its printed proof and Lean arithmetic already give denominator 14. The review’s strict denominator 12 is a minor local tightening. E.11 converts the auxiliary scale into a bound for every sufficiently large target size. [Shared gates](passes/pass13A-gate-reuse.md) · [Price and circuit estimates](passes/14a-flat.md)
3. In the contracting branch, H.1 constructs the tower and H.2 applies the G.2 identities, routes packets, preserves weighted values and accounts for resources. K.2 and K.3 take any small circuit and produce a bounded weighted evaluator for short plain instances. The concrete formal word polynomial can differ from the printed one away from its legal inputs. K.2 compiles an exact circuit for the clause polynomial. K.3 uses its degree bound and then invokes their common evaluations on canonical inputs. [Tower and laws](passes/14b-tower.md) · [Circuit compiler](passes/14c-compiler.md)
4. Follow the exact matching of field, size, scale and program in K.3 and K.6. The diagonal yields V=1+V in a nonzero ring. The separate membership witness places HC in VNP, and the exact lower bound excludes it from VP. [Arbitrary circuit to contradiction](passes/14e-circuit-to-contradiction.md) · [Rooted HC witness](passes/pass13D-membership.md)
5. Compare that mathematical reconstruction with the [complete-release verification record](passes/14d-formal.md) and the [coverage register](report/proof-coverage.csv). The native Lean rebuild compiled all 324 publisher sources, including the complete exact and approximate endpoints. The separate Linux run accepted all five public declarations with nanoda enabled. The proof-term checks and the remaining manuscript/implementation correspondence have distinct scopes. Reusable ideas are recorded in the [transferable-mechanism register](report/transferable-mechanisms.md).

## Reproduce Edition 12

Pass 15 follows the contracting branch from the [K.4 tally interpreter](report/pass15-k4.tex) through the [K.5 scale transfer](report/pass15-k5.tex) into the [K.6 diagonal](report/pass15-k6.tex). The [short reading guide](passes/15-diagonal.md) gives the exact line at which the proof first invokes the accelerator's conditional value clause. A separate Lean result sharpens the K.4 clock to the inclusive endpoint and identifies a family that overflows the counter at the next step.

Run the complete offline check from the repository root with Python 3.9 or later. It validates the publisher tree, earlier full-build and Comparator evidence, the new targeted receipt and report hashes. It runs the finite controls and validates the formal receipts without installing Lean. See the [check catalogue](checks/README.md) for per-script modes. The separate Lean command rebuilds the 16-module closure from source and checks the five review lemmas. It requires Lean 4.33.1 on the search path and the built mathlib checkout at the pinned dependency revisions.

~~~sh
python3 checks/check_all.py
python3 checks/pass09_endpoint_replay.py --mathlib "$MATHLIB_DIR" --target-module Paper.NoAcc --query-file checks/pass15_plain.lean --output /tmp/pass15-lean.json
python3 checks/pass14_report_rebuild.py --lualatex lualatex --output /tmp/vp-vnp-ed12.pdf
python3 checks/pass14_report_rebuild.py --verdict --lualatex lualatex --output /tmp/vp-vnp-verdict.pdf
~~~

Compare the rebuilt report with the release using the [Edition 12 PDF receipt](report/edition12-build.json). The shared builder fixes the build clock. Matching engine, fonts and packages are needed for byte identity. The [machine receipt](checks/pass15_lean.json) identifies all project sources compiled and the query used. Edition 11 supplies the separate complete-release Comparator run.

## Reproduce Edition 11

The [source lock](source-lock.json) identifies the publisher commit, 11b6c7e3c927df2658f513b6b68ea7f8929c62c5, original PDF and locked libraries. First run `python3 checks/pass14_reader_check.py` to verify the complete package offline. Run the three finite controls individually from the repository root with Python 3.9+ and its standard library. Each script emits deterministic JSON that can be compared with the corresponding checked-in result.

~~~sh
python3 checks/pass14a_flat.py
python3 checks/pass14b_tower.py
python3 checks/pass14c_compiler.py
~~~

For a fresh build of the entire original Lean project, install Lean 4.33.1 and prepare a built mathlib checkout and dependencies at the revisions in the [Lake manifest](primary/vp-vnp/lake-manifest.json). Set MATHLIB_DIR to its path. The runner checks all package revisions, builds from source into a previously absent directory, compares challenge and solution signatures in separate environments, and queries the permitted axiom dependencies. Pass the objects subdirectory shown below to check the review's separate /12 circuit theorem. The complete local-project build uses prebuilt external packages. [Release runner](checks/pass14_release.py) · [Independent arithmetic and circuit bridge](checks/pass14a_margin_replay.py)

~~~sh
python3 checks/pass14_release.py --mathlib "$MATHLIB_DIR" --jobs 3 --work-dir /tmp/vp-vnp-pass14-fresh --output /tmp/pass14-release.json
python3 checks/pass14a_margin_replay.py --mathlib "$MATHLIB_DIR" --objects /tmp/vp-vnp-pass14-fresh/objects --output /tmp/pass14-margin.json
~~~

The [original Linux build and Comparator logs](checks/pass14_linux_artifact.zip) are preserved with their GitHub artifact digest. For the hosted verification use the [pinned-project workflow](.github/workflows/pass14-comparator.yml). It checks the project and driver against their original Git objects, builds the default Lake targets on a disposable Linux runner and invokes the publisher's Comparator with the locked five-theorem configuration. The independent [Linux run 45691617731](https://github.com/nousentllc/VP-VNP-Review/actions/runs/45691617731) completed the unmodified driver and returned its exact acceptance marker. [Machine receipt](checks/pass14_comparator.json). The [formal track](passes/14d-formal.md) records which stages ran, their actual outcomes and evidence retention. The [publisher configuration](primary/vp-vnp/comparator.json) lists the five names, three permitted axioms and Nanoda setting.

Edition 11's original TeX, PDF, [build receipt](report/edition11-build.json) and complete source tree remain in the archived packet below. Extract that packet before rebuilding the historical PDF. Each edition has one editable TeX master, included fragments and the original Nous PNG directly below the cover subtitle.

## Review packets

[Download the Edition 12 packet](handoff/VP_VNP_Review_2026-11-25_pass15.zip). Its 509 files reproduce the research snapshot at `3d3d24a8d43836a6df80bc87bf483745aa66dc54`. Every member matched its Git blob. A clean extraction passed the full offline suite and rebuilt both the two-page verdict and 66-page technical report byte for byte. ZIP SHA-256 `b9c8124b1947998a78ddf2e7893d94392bba035ddd75bca76fc7babfdfda122b`. The packet includes the pinned publisher source, editable report and all receipts. Earlier handoff ZIPs are available separately below.

[Download the Edition 11 packet](handoff/VP_VNP_Review_2026-11-25_pass14.zip). Its 478 verified files reproduce the research tree at commit `bf956990d0f1f0002fa08989433ed51c32168b2a`, including the 53-page PDF, editable sources, publisher release and execution receipts. ZIP SHA-256 `637c97d243108169d22faec01a4d494c55a939fa56af810ca14ca43692031af6`.

The [archived thirteen-pass packet](https://github.com/nousentllc/VP-VNP-Review/blob/3754047be3854ef313df17ae5117c6ca5a66b4b8/handoff/VP_VNP_Review_2026-11-25_pass13.zip) preserves Edition 10 from research commit 4350383. Its ZIP SHA-256 is 06523551fe89e37d9b691c2ff05cf98a2cf65c646d1abb3a38ed381a17e09cea.

The [archived twelve-pass packet](https://github.com/nousentllc/VP-VNP-Review/blob/2f263c05d27afe803489583f94833e48a1ba972e/handoff/VP_VNP_Review_2026-11-25_pass12.zip) preserves Edition 9 from research commit `3973fb8`.

The [archived eleven-pass packet](https://github.com/nousentllc/VP-VNP-Review/blob/33edc6eb465bb2c565e82d3461fd418c1890d65e/handoff/VP_VNP_Review_2026-11-25_pass11.zip) preserves Edition 8 from research commit `e15d655`.

The [archived ten-pass packet](https://github.com/nousentllc/VP-VNP-Review/blob/3bf9cd5e052da8313c56e73b1346ad792dfeb95d/handoff/VP_VNP_Review_2026-11-25_pass10.zip) preserves the handoff from research commit `5ee75d1`.

The [archived nine-pass packet](https://github.com/nousentllc/VP-VNP-Review/blob/8295d58c59adeaa750235483330bba66475828c1/handoff/VP_VNP_Review_2026-11-24_pass09.zip) preserves the handoff from research commit `f6909ed`.

The [archived eight-pass packet](https://github.com/nousentllc/VP-VNP-Review/blob/7af4005af05cad5fac6ba184a24704b7b15f5465/handoff/VP_VNP_Review_2026-11-24_pass08.zip) preserves the handoff from research commit `8ee44fe`.

The [archived seven-pass packet](https://github.com/nousentllc/VP-VNP-Review/blob/ec35fabf2077827a470a6d02151da905cdef97aa/handoff/VP_VNP_Review_2026-11-24_pass07.zip) preserves the earlier handoff from research commit `c5d9ac1`.

The [archived six-pass packet](https://github.com/nousentllc/VP-VNP-Review/blob/84906e9ef713358863f195747b4e12c9a4371f06/handoff/VP_VNP_Review_2026-11-24_pass06.zip) preserves the earlier handoff from research commit `1bc85ed`.

## Earlier mathematical and formal records

- [Paper](primary/vp-vnp/paper.pdf) and [formal source](primary/vp-vnp/) from Claude (Anthropic). The `primary/` directory preserves the publisher’s files for offline reading. Its [license](primary/vp-vnp/LICENSE) and [attribution](primary/vp-vnp/NOTICE) accompany the source.
- [Source manifest](source-lock.json) identifying the exact publisher commit and the PDF’s SHA-256 digest. A checkout includes the same paper and proof files that the review cites.
- [Small algebra checks](checks/check_bounds.py), [recorded results](checks/results.json), and [publisher CI evidence](checks/upstream-ci.json). Run `python3 checks/check_bounds.py` to reproduce the algebra checks. Pass 5 adds [run-multiplicity checks](checks/pass05_traces.py), [source-language examples](checks/pass05_examples.lean) and [time-bound lemmas](checks/pass05_time.lean). The [pass record](passes/05-universal-automaton.md) gives their execution conditions and the scope of the independent Lean checks.
- [One-cut and iteration review](passes/06-one-cut-and-iteration.md) and [finite checks of weights and resource bounds](checks/pass06_cuts.py). Run `python3 checks/pass06_cuts.py` from this directory.
- [Theorem D.2 and field coverage](passes/07-field-alternative.md), with [exact finite checks](checks/pass07_geometry.py) and [reflection lemmas](checks/pass07_reflection.lean). Run `python3 checks/pass07_geometry.py` from this directory.
- [Proposition C.3 and price-space completion](passes/08-price-space-completion.md), with [exact midpoint examples](checks/pass08_midpoints.py) and [a local replay of the publisher’s two completion lemmas](checks/pass08_completion.py).
- [Theorem C.1, the curvature bound and its limits](passes/09-curvature-bound.md), with [finite-box boundary checks](checks/pass09_fan_boundary.py), [endpoint lemmas](checks/pass09_endpoint.lean), and the [full publisher-source replay](checks/pass09_endpoint_replay_results.json). The [portable replay script](checks/pass09_endpoint_replay.py) gives the toolchain and input requirements. Run `python3 checks/pass09_fan_boundary.py` from this directory.
- [Propositions A.7 and A.8, simultaneous extension](passes/10-simultaneous-extension.md), with [exact examples](checks/pass10_examples.py) and [formal statement and axiom queries](checks/pass10_formal.lean). The [24-module verification record](checks/pass10_formal_results.json) and [portable runner](checks/pass10_formal_replay.py) document the local replay. Run `python3 checks/pass10_examples.py` from this directory.

- Pass 11 comprises [crossing and curvature](passes/11a-crossing.md), [spectral selection](passes/11b-spectral-selection.md), [weighted piece decomposition](passes/11c-piece-decomposition.md), and [field transfer](passes/11d-field-transfer.md). Each record distinguishes general arguments, finite controls and machine-check scope.

- Pass 13 includes the [combined formal replay](passes/pass13E-branch-replay.md) alongside the four mathematical investigations. The complete section-by-section derivations and worked examples appear on pages 19–30 of the PDF.

- Pass 12 adds [contracting laws and stage load](passes/12a-contracting-laws.md), [the Hamiltonian-cycle projection](passes/12b-hamiltonian-projection.md), [the growing-dimension flat estimate](passes/12c-flat-estimate.md), and [crossing counts and signs](passes/12d-counting-and-minors.md). Each note links its original-source locations, reproducible checks and the specific evidence from Lean.

## Reading the technical appendix

The [Edition 12 handoff](VP_VNP_Chat_Handoff.md) records J.3–J.4 as an optional topic for readers studying how the cutter is implemented. K.5 uses the same cut to control encoding, list lengths and accepting times, then uses piece plainness to replace weighted values. The exact and approximation claims retain distinct hypotheses. RCMG and QFTN / Uriel-GEMA remain independent projects.

## TeX covers

Use the [original Nous PNG](report/nous-black.png) on the front page directly beneath the title and subtitle of each new or revised research TeX document.
