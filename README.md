# VP–VNP research review

Start with the [cumulative handoff for Chat](VP_VNP_Chat_Handoff.md). It gives the paper’s exact claim, what eleven review passes established, and four concrete proof questions for the next round. The [individual pass records](passes/) preserve the reasoning and manuscript references behind each finding.

The first Git checkpoint, `review-2026-11-24`, captures passes 1–4 together. The review predates the repository. For each subsequent pass, add its dated record under `passes/`, update the handoff to identify any finding that changed, and commit the two together.

[Read the cumulative research report (PDF)](report/VP_VNP_Research_Review.pdf) or [open its editable TeX source](report/VP_VNP_Research_Review.tex). The expanded edition includes four parallel audits across the geometry, flat branch, contracting branch and final field transfer. The [proof coverage map](report/proof-coverage.csv) links 43 claims, interfaces and verification steps to their roles, evidence and unresolved dependencies.

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

## How to continue the review

Run at least three distinct proof questions in parallel in each research round. Give each question a manuscript claim, a downstream consumer, and an explicit obligation the track can settle. Bring all tracks back into one cumulative report, update the coverage map and Chat handoff, and record which earlier conclusions gained support, changed, or remain conditional. The [handoff](VP_VNP_Chat_Handoff.md) lists the next four questions.

## TeX covers

Place the [Nous PNG](report/nous-black.png) on the front page directly beneath the title and subtitle of each new or revised research TeX document. The cumulative report illustrates the placement.
