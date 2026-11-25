# VP–VNP research review

This repository follows an independent review of the proposed lower bound for exact arithmetic circuits in *VP ≠ VNP Over Every Field*. The [Edition 10 research report (PDF)](report/VP_VNP_Research_Review.pdf) presents the derivations. The [cumulative Chat handoff](VP_VNP_Chat_Handoff.md) gives the current conclusions, their limits, and the next proof questions. The [51-entry coverage map](report/proof-coverage.csv) links each audited claim to the publisher’s source and our reasoning.

## A reader’s route

1. Start with Theorem 1.1 on p. 2 of the [archived manuscript](primary/vp-vnp/paper.pdf) and the [formal circuit definition](primary/vp-vnp/Statement.lean#L23). Fix a field, a matrix size, and a hypothetical small circuit. The target is an identity of formal polynomials.
2. Read the two projections side by side. The [HC construction](passes/12b-hamiltonian-projection.md) matches each assignment to one structural cycle. The [permanent construction](passes/pass13C-permanent.md) counts signed choices and normalizes a factor of two. In the report the calculation is carried out before its effect on circuit size is claimed.
3. Follow the field alternative into either branch. The [gate-reuse audit](passes/pass13A-gate-reuse.md) explains why reuse does not evade E.4’s charge per balanced cut. The [contracting-law audit](passes/pass13B-gain.md) derives the parameter order under which the common index fits each channel. The [field-alternative replay](passes/12e-field-alternative-replay.md) identifies the disjunction consumed here.
4. Read the [rooted HC witness](passes/pass13D-membership.md) to see why the family is in VNP over every field. M.4 additionally needs the proposed lower bound to place the family outside VP. Each track ends with the first further step its derivation still requires.

## Reproduce Edition 10

Run the following from the repository root. Python 3.9 or newer and its standard library suffice for this check. It verifies the pinned source tree, coverage anchors and recorded formal readbacks against the checked-out files, then reruns all four independent finite controls.

```sh
python3 checks/pass13_reader_check.py
```

To rerun a formal proof, install Lean 4.33.1 and prepare mathlib and its dependencies at the revisions in [the publisher’s manifest](primary/vp-vnp/lake-manifest.json). Set `MATHLIB_DIR` to that built mathlib checkout, with the other packages in its ordinary Lake package directory. With the pinned `lean` on your path, these commands build fresh project modules in a temporary directory. Change `--jobs` to suit available memory. Separate commands for the narrower replays appear in the pass notes.

```sh
python3 checks/pass13_joint_replay.py --mathlib "$MATHLIB_DIR" --jobs 3 --output /tmp/pass13-branches.json
python3 checks/pass09_endpoint_replay.py --target-module Nc.Hc.Vnp --query-file checks/pass13d_membership.lean --mathlib "$MATHLIB_DIR" --output /tmp/pass13-hc.json
```

The [editable master TeX](report/VP_VNP_Research_Review.tex) includes all body fragments by relative path. From a checkout with LuaLaTeX, Latin Modern fonts, and the listed TeX packages, rebuild into a separate directory. Two runs resolve page references and bookmarks. The front cover uses the archived Nous PNG directly beneath the title and subtitle.

```sh
mkdir -p /tmp/vp-vnp-review-pdf
(cd report && lualatex -halt-on-error -output-directory=/tmp/vp-vnp-review-pdf VP_VNP_Research_Review.tex && lualatex -halt-on-error -output-directory=/tmp/vp-vnp-review-pdf VP_VNP_Research_Review.tex)
```

The original pinned paper and proof files are in `primary/`. The [source lock](source-lock.json) identifies the publisher revision, licensing and pass-specific verification scopes. Evidence from formal builds, independent derivations, and finite examples is distinguished in the report and pass records.

## Review packets

The [archived twelve-pass packet](https://github.com/nousentllc/VP-VNP-Review/blob/2f263c05d27afe803489583f94833e48a1ba972e/handoff/VP_VNP_Review_2026-11-25_pass12.zip) preserves Edition 9 from research commit `3973fb8`.

The [archived eleven-pass packet](https://github.com/nousentllc/VP-VNP-Review/blob/33edc6eb465bb2c565e82d3461fd418c1890d65e/handoff/VP_VNP_Review_2026-11-25_pass11.zip) preserves Edition 8 from research commit `e15d655`.

The [archived ten-pass packet](https://github.com/nousentllc/VP-VNP-Review/blob/3bf9cd5e052da8313c56e73b1346ad792dfeb95d/handoff/VP_VNP_Review_2026-11-25_pass10.zip) preserves the handoff from research commit `5ee75d1`.

The [archived nine-pass packet](https://github.com/nousentllc/VP-VNP-Review/blob/8295d58c59adeaa750235483330bba66475828c1/handoff/VP_VNP_Review_2026-11-24_pass09.zip) preserves the handoff from research commit `f6909ed`.

The [archived eight-pass packet](https://github.com/nousentllc/VP-VNP-Review/blob/7af4005af05cad5fac6ba184a24704b7b15f5465/handoff/VP_VNP_Review_2026-11-24_pass08.zip) preserves the handoff from research commit `8ee44fe`.

The [archived seven-pass packet](https://github.com/nousentllc/VP-VNP-Review/blob/ec35fabf2077827a470a6d02151da905cdef97aa/handoff/VP_VNP_Review_2026-11-24_pass07.zip) preserves the earlier handoff from research commit `c5d9ac1`.

The [archived six-pass packet](https://github.com/nousentllc/VP-VNP-Review/blob/84906e9ef713358863f195747b4e12c9a4371f06/handoff/VP_VNP_Review_2026-11-24_pass06.zip) preserves the earlier handoff from research commit `1bc85ed`.

## Evidence in this edition

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

## How to continue the review

Run at least three distinct proof questions in parallel in each research round. Give each question a manuscript claim, a downstream consumer, and an explicit obligation the track can settle. Bring all tracks back into one cumulative report, update the coverage map and Chat handoff, and record which earlier conclusions gained support, changed, or remain conditional. For every new mathematical result, include the objects and assumptions, the step-by-step derivation, the effect of at least one changed hypothesis where informative, its direct proof consumer, exact source references and a runnable check where appropriate. The [handoff](VP_VNP_Chat_Handoff.md) lists the next four questions.

## TeX covers

Place the [Nous PNG](report/nous-black.png) on the front page directly beneath the title and subtitle of each new or revised research TeX document. The cumulative report illustrates the placement.
