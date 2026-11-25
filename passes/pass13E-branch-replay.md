# Pass 13E · What the joint formal replay covers

The mathematical routes in 13A and 13B meet two full publisher modules. Paper.Flat contains the balanced coefficient decomposition and the construction of cut tensors. Paper.Laws proves the existence and resource bounds for the law menu. The build tests the original theorem bodies in their original import context.

## Locked input, build and readback

The runner checks the Git tree object for all 333 files in the archived source subtree, checks the nine external checkout revisions, checks the compiler version, and opens an empty object directory. It schedules a publisher module only after all of its publisher prerequisites have compiled successfully. Each source hash and the full statement/axiom transcript are recorded. Prebuilt objects for Lean and the pinned external libraries are used as imports. [Publisher pin](../source-lock.json) · [Runner](../checks/pass13_joint_replay.py) · [Declaration queries](../checks/pass13_joint.lean) · [Receipt](../checks/pass13_joint_replay.json)

Paper.Flat requires 115 publisher modules and Paper.Laws requires 113. Their intersection contains 110, so the union requires 118. A single fresh build pays for each once. The twenty queries read back ten statement types and their axiom dependencies: polynomial and coefficient forms of E.4, the mixed-cut tensor sum, the Poincaré input, the tensor cover, laws over the field, G.2 with its uniformity, the existential integer-degree specialization, and the general F.6 and A.6 inputs. The named axioms are propositional extensionality, classical choice and quotient soundness. The formal types and their complete hypotheses can be read in the receipt.

The endpoint modules do not import the numerical flat theorem in Paper.Rate, the general tree application in Paper.Tree, the terminating program argument in Paper.NoAcc, or the family-level corollary in Paper.Fields. Formal evidence for the price-space field alternative was recorded separately in [12E](12e-field-alternative-replay.md). A pass on the full formal challenge and an independent Comparator run remain open. The individual records state which implications were also reconstructed mathematically, and which were tested only on finite controls. [Gate decomposition](pass13A-gate-reuse.md) · [Field gain](pass13B-gain.md)

## Reproduction

Set MATHLIB_DIR to the pinned, built checkout. Put Lean 4.33.1 on the path. Run from the review root. The first command compiles fresh source and writes a separate receipt; the second uses the archived receipts, without recompiling, and reruns the four exact finite controls.

```sh
python3 checks/pass13_joint_replay.py --mathlib "$MATHLIB_DIR" --output /tmp/review-pass13-joint.json
python3 checks/pass13_reader_check.py
```
