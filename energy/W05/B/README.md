# Rebuild W05-B

Run from the W05 directory. The source of the W04 AIPC contract, the Lean toolchain file and the original nine-package Lake lock are in B/formal. The release run rebuilt W04's AIPC source and every W05 module in a fresh temporary directory with Lean 4.30.0-rc2. The external mathlib commit is 896cc56a395e1615786fac56564a3fe6bfeebcc4. The transitive library cache was already built. Interpreting the proof result trusts the compiler and that cache, and the correspondence of deployed numerical data to the stated mathematical model.

A second clean replay reproduced all nine archived proof logs and JSON records byte for byte. Run the exact finite controls with any recent Python 3 supporting zip(strict=True).

    python3 B/exact_controls.py

Run the independent rational check of the engineering lift, block maps, candidate and uniform constants, and regret interval with Python and NumPy. Its result is recorded in `B/results/engineering_crosscheck.json`.

    python3 B/audit_engineering.py

For Lean, set LEAN_BIN to the actual pinned lean executable and PACKAGES to its Lake dependency-checkout directory. Each checkout must be at the exact revision in B/formal/lake-manifest.json and have its compiled library at .lake/build/lib/lean. The driver checks every Git revision, tracked change status and locked proof-source hash. Use a new path for the output.

    python3 B/verify.py --lean "$LEAN_BIN" --packages "$PACKAGES" --out /tmp/crgc-w05-b-proof

A user with elan, Git and network access can prepare dependencies in a disposable copy of B/formal using its lean-toolchain and lake-manifest.json, fetching the locked checkouts and running lake exe cache get in that copy. Locate the matching compiler with elan which lean and the checkout directory at .lake/packages. Should local checkout paths be unresolved, lake update in this disposable copy followed by lake exe cache get can populate them. The verified pins in the delivered proof lock still apply. This cold network bootstrap was not part of the campaign. Include the commit-locked mathlib source/library closure to replicate without network access.

## Proof artifacts

- formal/Anchor.lean implements the scalar ratio with explicit empty and zero-slack conventions. Its minimum-fraction equivalence covers every possible segment weight in [0,1]. It instantiates the rows on actual affine maps and the convex base, covers equality repair and derives the manuscript's Lipschitz bound on that base.
- formal/Transfer.lean proves the affine box support for a computable α, a scaled uniform β product, the required surrogate mismatch, and composition with W04.
- formal/Terminal.lean proves the row capacity test, signed single-slot terminal-energy feasibility, SOC suffix effect, ramp identities, loss accounting and a two-slot obstruction to declaring infeasibility from single-slot failure.
- formal/Obstructions.lean supplies explicit data for equality mismatch, unusable anchors, nonconvex and integral modes, lost inequalities, and bounds from restricted domains. It also includes the two-anchor stress example.
- formal/FalseVariants.lean contains seven intentionally false claims. The nonzero compiler result is expected. The validator requires diagnostics on exactly the seven declared lines and checks corresponding positive obstruction evidence. A missing import or generic compile failure does not fulfill this test.
- results/lean/Inventory.log records exact types, their transitive axioms, and 77 in-project theorem/helper nodes with direct dependency lists. The compiler checked 40 new theorems. Every reported theorem uses only propext, Classical.choice and Quot.sound. The formal modules starting with AIPC through Inventory exited successfully. The numerical solver and constructed engineering matrices are outside these declarations.
- results/exact_controls.json is the deterministic rational audit. The same file is regenerated under results/lean. Test dimensions and engineering scope appear in FINDINGS.md. Source fingerprints and proof compilation outcomes appear in proof_lock.json and results/lean/proof_audit.json.
- results/development_compile_failures.log records the failed exploratory proof drafts. The errors were elaboration issues addressed before the locked build. Negative mathematical results and their explicit witnesses remain in Obstructions.lean, FalseVariants.lean and EXPLORATORY.md.

FINDINGS.md explains the model, proofs and gaps. LITERATURE.md identifies primary sources and the relation to prior work. EXPLORATORY.md separates the two-anchor construction from the registered engineering evaluation. The exact reproduction of mathematical tests uses no empirical seed. The engineering panel and its independent clock measurements are documented in the associated numerical track.
