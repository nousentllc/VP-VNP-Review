# Reproduce W06-B

The source and proof environment are pinned in [proof_lock.json](proof_lock.json) and [formal/lake-manifest.json](formal/lake-manifest.json). Python's standard library is sufficient for finite rational controls. From the W06 directory, run the commands below.

    python3 B/exact_controls.py > /tmp/crgc-w06b-exact.json
    cmp /tmp/crgc-w06b-exact.json B/results/exact_controls.json

For Lean, use a fresh output directory and the executable and packages checkout matching [formal/lean-toolchain](formal/lean-toolchain) and the nine Git revisions in the manifest.

    python3 B/verify.py --lean "$LEAN_BIN" --packages "$PACKAGES" --out /tmp/crgc-w06b-check --replay-oleans

The W06 run reused the pinned W05 package checkout with precompiled artifacts. The eight available package build directories and all nine source revisions are recorded in the proof audit. The pinned Cli source has no separate build directory in this environment and was not required for the W06 modules. A cold bootstrap can use a disposable copy of B/formal, an installation of elan and Git, and the pinned toolchain and Lake manifest. Populate the package checkouts and caches there, for example with `lake exe cache get`. Set LEAN_BIN to the path from `elan which lean` inside this pinned environment and PACKAGES to its absolute `.lake/packages` path. The cold network bootstrap was not tested here. Prebuilt libraries, compiler and package sources are external dependencies.

The driver checks source hashes and tracked checkout revisions, builds every positive module with one compiler thread, checks diagnostics at the eight intended false statements, inspects all transitive axioms and reruns the rational controls. The optional OLean replay invokes the distributed `leanchecker` on each of the four positive theorem modules, using its imported environment and the same Lean kernel. This provides a second pass over those declarations. Compiler binary hashes are machine-specific and the driver pins the source revision and release. The wall-time record varies between runs. The compiled intermediate files exist only in a temporary directory.

[Findings](FINDINGS.md) · [Literature](LITERATURE.md) · [Claim register](claims.csv) · [Diagnostic logs](results/lean/) · [Recorded development failures](results/development_failures.txt)

A separately locked [flat-tariff addendum](flat_review/README.md) provides twelve further mathematical declarations and a historical data replay. Its logs and source hashes are independent artifacts alongside the original core build.
