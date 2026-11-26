# Repository privacy review — 26 November 2026

## Finding and disposition

No actual credential was identified by the tested rules and candidate review. This is a bounded screening result, not a guarantee that unknown or encoded secrets are absent. A personal author email remains in historical Git author/committer and annotated-tag metadata. Its value is deliberately omitted. Local workstation account paths also survive in historical logs and source records. Names and experimental spending were allowed by the owner and were not redacted.

The active `source-lock.json` workstation path is replaced with a neutral description; the paper SHA-256 and the recorded byte-equality finding remain. The original index, logs, archives, report and Git objects remain in the preserved history and local restricted backup. Historical verification transcripts are immutable evidence; their account-path occurrences are disclosed rather than silently edited while retaining obsolete hashes. The new publication excludes private backups, Git metadata and build caches. New publication commits use the verified account's GitHub noreply address.

**Residual exposure:** the personal email remains publicly retrievable through commit/tag history. Removing it would require a separately approved history rewrite and coordinated handling of old clones, tags and cached pages. No force-push, history rewrite or visibility change was performed. No exposed credential was confirmed, so this review does not prescribe rotation of an unidentified key. If a credential is subsequently confirmed, revoke or rotate it first; deleting a current file would not revoke the credential or remove historical copies.

## Reachable-history coverage

The baseline scan includes 44 commits, 452 trees, 2 annotated tag objects and 2,861 blobs reachable from all fetched local/remote refs. The public main tip at that snapshot is `3a612bdfb160a45c26d016364c2e9195b5e1f7b1`; the historical `energy-explorations` tip is `d31745351533a90d4c6e158036d84d14a56cc037`. Both release tags and the retained local reconciliation branch are included. The machine-readable ref inventory identifies every scanned tip. Advertised pull refs were queried; none were returned. No GitHub release assets were listed by the releases API at review time.

The scan follows nested content, rather than only filenames. It covers 117 unique ZIP containers, 668 gzip containers, 219 NumPy arrays (213 numeric and six string arrays), 28 unique PDFs including the recovered and expanded publication, two raster images by OCR, and five PDF attachments containing JUMBF/C2PA manifests (20 CBOR boxes). PDF text, document metadata, XMP, attachment listings and extracted attachments were screened. The C2PA payloads were decoded for text and binary strings; their cryptographic authenticity was not assessed. Content is deduplicated by SHA-256, so repeated archive copies are screened once. Approximately 550 MB of distinct encountered content was processed; this count includes container bytes and their decoded members, not 550 MB of independent evidence.

Rules cover common provider credential prefixes, temporary AWS identifiers, bearer values, embedded URL authentication, assigned secrets, private-key headers, JWT-like tokens, email candidates, workstation paths, private network addresses, labeled personal fields, US SSN patterns and parenthesized US phone patterns. Every candidate category returned was reviewed. The scanner does not send candidate values to a service or test whether any credential is live.

## Candidate classification

- The author email in Git metadata is a real personal identifier. It is not an API key.
- Lean escaped-newline/namespace expressions containing `@` are syntax, not email addresses. Python `@` expressions are matrix multiplication, not email addresses.
- Three third-party professional contact addresses occur as public attribution in imported PGLib/MATPOWER benchmarks. They are preserved with the benchmark provenance, not treated as the owner's private data.
- Local user home paths identify a workstation account. Runner/proof environment paths are system paths, not evidence of another person's identity.
- Allowed author names, research budgets, experiment costs, timestamps and mathematical/numerical data are not redacted merely because a broad detector could match them.

The public candidate register records locations, categories and content hashes without matched values or hashes of the personal email itself. The complete byte inventory and scan rules support repeatable review. A detector's initial classification is not substituted for this adjudication.

## One incomplete compressed member

The following historical member is truncated:

`energy/Archives/W04/W04_Energy_Experiments.zip` → `W04/D/serial_raw/ca_2014-12-01_reserves_1_48_group_start/columns.json.gz`

Its compressed-byte SHA-256 is `69e5603f1808ccbaab1746280189179086e0932fa5d7e62edb353155a0d33f73`. The scanner recovered and screened the available decompressed prefix. The missing tail cannot be reconstructed or cleared by this scan. The original archive is preserved. No other container extraction limit was recorded in this run.

## Preservation and limits

A restricted local Git bundle preserves the complete reviewed history. The initial bundle SHA-256 is `9d30396c72499d1aec50bc0ab10f2544105627a71555ebe29888d2dde26320d1`; the refreshed all-ref bundle SHA-256 is `c5266e72945cd334fe11f4fb212301629064c11181dcb517ecb1363079678cb7`. Git bundle verification passed. The parent directory has owner-only access and bundle files have owner-only read/write permission. These are access-controlled originals, not an assertion of encryption at rest, and are excluded from the public ZIP.

Scope does not include deleted/unreachable server objects, other people's clones or forks, GitHub caches, unarchived external Actions logs, secret/account settings, or any unavailable original ChatGPT ZIP. Pattern screening and OCR can miss unfamiliar credential formats, unlabeled identifiers, handwriting, obfuscated values and covert encodings. Numeric arrays are classified as numerical data without attempting to reinterpret every measurement as a personal identifier. The scanner's archive depth and member-size guards are documented in its source; neither produced an additional limit in this run. No malware execution or credential validity testing was performed.

The publication payload receives a final scan after assembly. Its receipt distinguishes that payload from the frozen baseline history counts, avoiding a claim that a report scanned its own future bytes.
