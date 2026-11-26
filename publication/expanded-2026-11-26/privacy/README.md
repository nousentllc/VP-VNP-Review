# Privacy evidence

`scan-summary.json` and `inventory.json` describe the frozen reachable-history scan and the publication payload at that scan. `candidate-register.json` contains value-suppressed locations and human-readable adjudications; `adjudication-counts.json` summarizes them. The personal email value and its fingerprint are omitted. `limits.json` identifies the single truncated member.

To repeat a scan with Git, Python, NumPy, Poppler (`pdftotext`, `pdfinfo`, `pdfdetach`) and Tesseract available on PATH:

```sh
python3 privacy_scan.py /path/to/repository /path/to/private-output
```

An optional third argument names a publication directory to screen before committing it. It skips build caches, Git internals and its own `privacy/` reports. Git history itself is read through `git cat-file`; nested archive members are decoded in memory, and PDF/image tools receive temporary files. The scan does not execute archive contents. Output contains no matched credential or email values, but its locations can still be sensitive; review before publishing. The baseline output was adjudicated for Lean syntax, matrix multiplication, public benchmark attribution and actual author metadata as explained in `../PRIVACY.md`.

The final payload receipt is a separate snapshot. No report can certify the bytes of its own future revision; package hashes and the delivery commit close that record.
