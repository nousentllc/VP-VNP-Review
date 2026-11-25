# Energy explorations

The **energy-explorations** branch of the private VP-VNP-Review repository holds the energy experiments in the energy directory. Each study keeps its own inputs, evaluation protocol, code, outcomes and evidence records.

| Study | Scope | Results and replay |
|---|---|---|
| W03 | Battery grouping, formal verification, AC power flow, unit commitment and forecast-aware computing load | [Results report](W03/REPORT.md) · [PDF](W03/W03_Results.pdf) · [Reproduction instructions](W03/README.md) |
| W04 | BESS warm starts, AIPC, stochastic control, AC-OPF and generator grouping | [PDF](W04/W04_Results.pdf) · [Evidence ledger](W04/claims.csv) · [Reproduction instructions](W04/README.md) |
| W05 | AIPC reconstruction and bounds, prediction and continuation value, BESS and AC-OPF | [PDF](W05/W05_Results.pdf) · [Evidence ledger](W05/claims.csv) · [Reproduction instructions](W05/README.md) |
| W06 | Certified opportunity assessment for storage, AC power flow and unit commitment | [PDF](W06/W06_Results.pdf) · [Evidence ledger](W06/claims.csv) · [Reproduction instructions](W06/README.md) |

The subsequent W05 opportunity review reuses the archived W05 scenarios. [Review](Reviews/W05/Independent_Opportunity/README.md) · [Replay verification](Reviews/W05/Independent_Opportunity/verification.json) · [v0.5 manuscript](Manuscripts/v0.5/CRGC_Whitepaper_v0.5.pdf)

## Manuscripts and release archives

The integrated v0.5 release includes the [editable LaTeX source](Manuscripts/v0.5/CRGC_Whitepaper_v0.5.tex) and [supplied PDF](Manuscripts/v0.5/CRGC_Whitepaper_v0.5.pdf). [Manuscript history](Manuscripts/) includes both v0.2 editions. The [originating proposal](Origin/) predates the experiments.

The W05 archive contains the sibling W04 directory used in replay. To repeat the subsequent opportunity review, run the following command from this directory with NumPy and SciPy installed.

```sh
python3 Reviews/W05/Independent_Opportunity/opportunity_review.py Archives/W05/W05_Energy_Experiments.zip /tmp/crgc-w05-opportunity-results.json
```

[W06 experiment ZIP](Archives/W06/W06_Energy_Experiments.zip) · [W06 verification](Archives/W06/W06_Archive_Verification.json) · [Original opportunity review ZIP](Archives/W05/CRGC_W05_Independent_Opportunity_Review.zip) · [W05 experiment ZIP](Archives/W05/W05_Energy_Experiments.zip) · [W04 experiment ZIP](Archives/W04/W04_Energy_Experiments.zip) · [W03 experiment ZIP](Archives/W03/W03_Energy_Experiments.zip)

Check the original manuscripts, ZIPs, review and experiment manifests from this directory with `shasum -a 256 -c RELEASE_SHA256SUMS.txt`. Each experiment's own manifest covers its individual files. The private Downloads collection also retains the cross-project Library and Drive inventories and the local filing history.
