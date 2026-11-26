# Expanded academic audit — 26 November 2026

The [76-page academic manuscript](VP_VNP_Expanded_Academic_Audit.pdf) expands the recovered 42-page draft against the complete Edition 12 source, all fifteen audit passes, all 63 claim entries, the pinned 70-page publisher manuscript and the J.4 follow-up. It is a review manuscript, not a public preprint submission or an independent discovery of the publisher's theorem.

- [Editable single LuaLaTeX source](VP_VNP_Expanded_Academic_Audit.tex)
- [Complete publication ZIP](https://github.com/nousentllc/VP-VNP-Review/raw/refs/heads/main/publication/VP_VNP_Expanded_Audit_2026-11-26.zip)
- [Claim-by-claim coverage delta](coverage-delta.csv) and [editorial account](COVERAGE.md)
- [Privacy review and remaining exposure](PRIVACY.md)
- [Source-corpus hashes](source-corpus.json), [verification receipt](verification.json) and [link checks](link-check.json)
- [Preserved recovered 42-page PDF](recovered/VP_VNP_Academic_Audit_42pp_Recovered.pdf) and [TeX](recovered/VP_VNP_Academic_Audit_42pp_Recovered.tex)
- [Original 66-page Edition 12](../../report/VP_VNP_Research_Review.pdf), [its source](../../report/VP_VNP_Research_Review.tex), [J.4 follow-up](../../followups/j4/README.md) and [historical execution evidence](../../history/actions/README.md)

The downloadable ZIP contains this publication directory and a repository source snapshot with the original report, all passes, the claim register, pinned publisher sources, checks and historical receipts. It excludes Git history, local private backups, font caches and temporary build logs. The separate `energy-explorations` branch was included in the privacy review but is not duplicated into the mathematical publication ZIP.

After extracting the ZIP, run `python3 publication/expanded-2026-11-26/verify_package.py` from its repository root to verify every listed payload file. The outer ZIP hash and source commit are recorded in the repository's delivery receipt.

## Rebuild and check

Install LuaLaTeX with Latin Modern fonts and the packages named in the TeX preamble (a full TeX Live installation supplies them). From this directory run:

```sh
sh build.sh
python3 verify_examples.py
```

The build uses three passes, disables shell escape, keeps font caches under `build/`, and fixes the PDF timestamp. `LATEX_ENGINE` can point to a LuaLaTeX executable. The verified environment is LuaHBTeX 1.24.0 / TeX Live 2026. The clean-copy comparison is in `verification.json`: page content streams and extracted text match; complete PDF bytes differ in the automatically generated document identifier. Other TeX/font versions can change pagination or output bytes.

From the repository root run `python3 checks/check_all.py`. This validates the original source custody and receipts and reruns 24 finite controls. The full proof reproduction paths remain in [REPRODUCE.md](../../REPRODUCE.md). This publication session did **not** run a fresh Lean or Comparator build. The manuscript distinguishes archived native/hosted proof runs, new finite calculations, explanatory reconstruction and pending independent human assessment.

The original recovered files are preserved byte for byte as supplied on 26 November. An unavailable earlier ChatGPT sandbox package cannot be assigned those same hashes retrospectively. This is a newly assembled, verified delivery package, not a claim to have recovered the original ZIP bytes.

Written review material is CC BY 4.0; review scripts are MIT. Publisher material retains its Apache-2.0 license and notice. The original Nous logo is included unchanged for the requested manuscript identity; no separate logo license is inferred. See the repository license files for inherited material.
