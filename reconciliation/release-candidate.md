# Edition 12 release candidate

This release prepares a verification and reproducibility report on Anthropic's published VP ≠ VNP formalization. The publisher's manuscript credits Claude, Anthropic, and describes the discovering system as an internal research Claude model. The review examines the correspondence between the printed statements and the pinned formalization, and documents two wording errata concerning K.3 and I.1. [Publisher manuscript](../primary/vp-vnp/paper.pdf).

## Contributions and verification status

- Justin Candler directed the review and is the human responsible for the release. Uriel, the project's AI research agent operating through OpenAI Codex, prepared the derivations, checks and statement correspondence analysis. The release-candidate tooling was prepared with GPT‑6.2 Sol. Earlier passes lack a verified per-pass model inventory. The human author should check the final disclosure and paper before submission.
- Anthropic Claude supplied the external Edition 11 critique. The exact Claude model and snapshot are absent from the recorded feedback. This critique is an AI reading. It does not supply an operator or receipt for third-party Tier 1 or Tier 2 runs. [Response to critique](edition12-external-review.md).
- Lean and nanoda accepted the publisher's five public declarations in the preserved review-team Linux run. The review's statement audit identifies the circuit, witness and border approximation models. The human review credit and third-party kernel reproduction fields remain pending. [Preserved job evidence](../history/actions/README.md) · [Statement correspondence](../passes/statement-correspondence.md) · [Errata](../passes/publisher-errata.md).

## Invitation for an independent reproducer

We’re looking for a Lean user outside the review team to reproduce our verification of Anthropic’s VP ≠ VNP formalization. The full source and the three commands are in the [Edition 12 release candidate](https://github.com/nousentllc/VP-VNP-Review/tree/v1.0-edition12-rc1). Tier 0 takes about a minute with standard Python. Tiers 1 and 2 use a pinned container and check the review’s Lean files and the publisher’s full build with Comparator and nanoda. Please report the exact commit, your platform, the final output lines and evidence hashes, including any failures. Let us know whether we may credit your name or handle and the run date. If you also read the statement correspondence, please say which sections you checked so we can credit that work separately. [Commands and expected evidence](https://github.com/nousentllc/VP-VNP-Review/blob/v1.0-edition12-rc1/REPRODUCE.md).

## Final release gates

1. Collect and verify the independent operator's dated transcript and hashes for the three tiers. Record attribution with permission. Record any human statement reading with its actual scope.
2. Send the two wording errata to the publisher with the minimal counterexamples and wording suggestions. Record the correspondence and distinguish proposed errata from any publisher response.
3. Reserve a version DOI in a Zenodo draft and insert it in the final TeX and citation metadata before rebuilding the PDFs and tagging `v1.0-edition12`. Include the full tagged repository source, archived CI evidence and independent reproduction receipt in the deposit, then publish and verify the DOI. Submit the final tag to Software Heritage and record its resolved revision identifier. [GitHub–Zenodo archiving](https://docs.github.com/en/repositories/archiving-a-github-repository/referencing-and-citing-content) · [Software Heritage Save Code Now](https://archive.softwareheritage.org/save/).
4. Submit the source package to arXiv under the human author's account after the final evidence and contribution statement are verified. Use cs.CC with cs.LO cross-list as the proposed routing, subject to arXiv's submission process. [Submission overview](https://info.arxiv.org/help/submit/index.html).
