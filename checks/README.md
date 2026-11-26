# Run the research checks

From the repository root, Python 3.9 or later can rerun all 24 standalone finite mathematical controls and verify the archived formal evidence and cumulative report. These commands also work in an extracted handoff with its original directory layout.

```sh
python3 checks/check_all.py
python3 checks/check_all.py --finite-only
python3 checks/check_all.py --receipts-only
```

**What runs locally.** Each finite script executes with assertions enabled. The first 18 script digests and stdout digests come from the Pass 14 prior-controls register. For the three controls introduced in Pass 14 and three introduced in Pass 15, the suite compares fresh stdout to the bytes of the result JSON. A failed assertion, missing result or output mismatch makes the command fail. Edition 11 contained 21 standalone finite mathematical controls under this counting rule. The separate Edition 11 source-pin verifier tests source and receipt integrity.

**What the archived evidence establishes.** The suite recomputes the publisher Git tree from 333 files, verifies the paper digest, and checks 47 historical inputs and records against SHA-256 values taken from the preserved Edition 11 packet. For the Comparator receipt it verifies the exact archived copy and compares every historical field with the annotated current receipt. The full native build and Linux Comparator validators also inspect source hashes, signatures, permitted axiom readbacks and the original hosted artifact. The Pass 15 validator checks the 16-module reconstruction and its 13 declarations against the current query. The final reconciliation checks the Comparator evidence and the numerical margin; it is logged separately from the 24 finite mathematical controls. A local run of these validators verifies records of earlier compiler and kernel executions. It performs no new Lean build.

## Select one recorded Lean investigation

Each of the ten Python launchers that normally invokes Lean accepts `--offline` by itself. It checks the source tree and the named investigation’s recorded evidence. The generic launcher also accepts `--target-module` in this mode for an archived target, including `Paper.NoAcc`.

```sh
python3 checks/pass08_completion.py --offline
python3 checks/pass10_formal_replay.py --offline
python3 checks/pass09_endpoint_replay.py --offline --target-module Paper.NoAcc
python3 checks/pass14_release.py --offline
```

| Launcher in this directory | Historical evidence selected |
| --- | --- |
| `pass08_completion.py` | C.3 completion excerpt digest and the written two-lemma record. This execution retained no independent JSON transcript. |
| `pass09_endpoint_replay.py` | `Paper.Fan` and its endpoint readbacks by default. Append `--offline --help` to list the other recorded targets. |
| `pass10_formal_replay.py` | Prices module, A.7/A.8 queries and recorded closure |
| `pass11c_replay.py` | Grouping and heavy-piece closures with their queries |
| `pass12a_law_replay.py` | Law-power and code-gluing excerpt receipt |
| `pass12c_replay.py` | Rate excerpts and independent budget proof |
| `pass13_joint_replay.py` | Combined flat-branch and law closures |
| `pass13a_gate_replay.py` | Gate-induction closure and the additional E.4 excerpt |
| `pass14_release.py` | The complete native project build, signature comparison and axiom records |
| `pass14a_margin_replay.py` | The numerical margin and its circuit bridge to the native `Paper.Rate` object |

For a fresh Lean run, omit `--offline` and supply each launcher's usual inputs. For instance, after putting Lean 4.33.1 on the path and setting `MATHLIB_DIR` to the built checkout at the publisher's pins, dedicate a previously unused output directory to the full native build. Then use its objects for the circuit bridge.

```sh
python3 checks/pass14_release.py --mathlib "$MATHLIB_DIR" --jobs 3 --work-dir /tmp/vp-vnp-fresh --output /tmp/vp-vnp-fresh-build.json
python3 checks/pass14a_margin_replay.py --mathlib "$MATHLIB_DIR" --objects /tmp/vp-vnp-fresh/objects --output /tmp/vp-vnp-fresh-margin.json
python3 checks/pass09_endpoint_replay.py --mathlib "$MATHLIB_DIR" --target-module Paper.NoAcc --query-file checks/pass15_plain.lean --output /tmp/vp-vnp-fresh-diagonal.json
```

Reproducing the hosted two-kernel check requires the separate Linux workflow and publisher-pinned checker tools. The historical compiler receipts remain available without any of these external dependencies. [Linux workflow](../.github/workflows/pass14-comparator.yml) · [Publisher package pins](../primary/vp-vnp/lake-manifest.json) · [Offline evidence index](offline-evidence.json)
