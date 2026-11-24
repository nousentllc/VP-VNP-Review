# VP–VNP research review

Start with the [cumulative handoff for Chat](VP_VNP_Chat_Handoff.md). It gives the paper’s exact claim, what the four review passes established, and the next proof obligation. The [individual pass records](passes/) preserve the reasoning and manuscript references behind each finding.

The first Git checkpoint, `review-2026-11-24`, captures passes 1–4 together. The review predates the repository. For each subsequent pass, add its dated record under `passes/`, update the handoff to identify any finding that changed, and commit the two together.

## Evidence in this edition

- [Paper](primary/vp-vnp/paper.pdf) and [formal source](primary/vp-vnp/) from Claude (Anthropic). The `primary/` directory preserves the publisher’s files for offline reading. Its [license](primary/vp-vnp/LICENSE) and [attribution](primary/vp-vnp/NOTICE) accompany the source.
- [Source manifest](source-lock.json) identifying the exact publisher commit and the PDF’s SHA-256 digest. A checkout includes the same paper and proof files that the review cites.
- [Small algebra checks](checks/check_bounds.py), [recorded results](checks/results.json), and [publisher CI evidence](checks/upstream-ci.json). Run `python3 checks/check_bounds.py` to reproduce the algebra checks. Independent Lean replay remains open.
