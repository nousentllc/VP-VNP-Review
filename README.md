# VP–VNP research review

Start with the [cumulative handoff for Chat](VP_VNP_Chat_Handoff.md). It gives the paper’s exact claim, what the nine review passes established, and the next proof obligation. The [individual pass records](passes/) preserve the reasoning and manuscript references behind each finding.

The first Git checkpoint, `review-2026-11-24`, captures passes 1–4 together. The review predates the repository. For each subsequent pass, add its dated record under `passes/`, update the handoff to identify any finding that changed, and commit the two together.

[Read the cumulative research report (PDF)](report/VP_VNP_Research_Review.pdf) or [open its editable TeX source](report/VP_VNP_Research_Review.tex). The report updates Edition 5 of the Markdown handoff through pass 9.

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
- [Theorem C.1, the curvature bound and its limits](passes/09-curvature-bound.md), with [finite-box boundary checks](checks/pass09_fan_boundary.py) and [endpoint lemmas](checks/pass09_endpoint.lean). Run `python3 checks/pass09_fan_boundary.py` from this directory.

## TeX covers

Place the [Nous PNG](report/nous-black.png) on the front page directly beneath the title and subtitle of each new or revised research TeX document. The cumulative report illustrates the placement.
