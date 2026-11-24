# VP–VNP research review

Start with the [cumulative handoff for Chat](VP_VNP_Chat_Handoff.md). It gives the paper’s exact claim, what the six review passes established, and the next proof obligation. The [individual pass records](passes/) preserve the reasoning and manuscript references behind each finding.

The first Git checkpoint, `review-2026-11-24`, captures passes 1–4 together. The review predates the repository. For each subsequent pass, add its dated record under `passes/`, update the handoff to identify any finding that changed, and commit the two together.

[Download the complete pass 6 packet](handoff/VP_VNP_Review_2026-11-24_pass06.zip). It contains the sources, checks, and handoff from research commit `1bc85ed`.

## Evidence in this edition

- [Paper](primary/vp-vnp/paper.pdf) and [formal source](primary/vp-vnp/) from Claude (Anthropic). The `primary/` directory preserves the publisher’s files for offline reading. Its [license](primary/vp-vnp/LICENSE) and [attribution](primary/vp-vnp/NOTICE) accompany the source.
- [Source manifest](source-lock.json) identifying the exact publisher commit and the PDF’s SHA-256 digest. A checkout includes the same paper and proof files that the review cites.
- [Small algebra checks](checks/check_bounds.py), [recorded results](checks/results.json), and [publisher CI evidence](checks/upstream-ci.json). Run `python3 checks/check_bounds.py` to reproduce the algebra checks. Pass 5 adds [run-multiplicity checks](checks/pass05_traces.py), [source-language examples](checks/pass05_examples.lean) and [time-bound lemmas](checks/pass05_time.lean). The [pass record](passes/05-universal-automaton.md) gives their execution conditions and the scope of the independent Lean checks.
- [One-cut and iteration review](passes/06-one-cut-and-iteration.md) and [finite checks of weights and resource bounds](checks/pass06_cuts.py). Run `python3 checks/pass06_cuts.py` from this directory.
