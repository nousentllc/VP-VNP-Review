# Reproduce Edition 12

Run each command from the root of the release-candidate checkout. The tiers answer different questions. Compare the hashes in the evidence table and report the pinned Git commit with your results.

| Tier | Command | Requirements and planning time |
|---|---|---|
| 0 | `python3 checks/check_all.py` | Python 3.11 or later, standard library only, about one minute. Validates source custody and stored receipts and reruns 24 finite controls. |
| 1 | `bash reproduce/run.sh 1` | Bash and Docker on Linux/amd64, Lean 4.33.1 and the pinned Mathlib cache inside the image. Allow up to an hour for a cold run. Compiles all 23 review Lean files after building their pinned publisher imports. |
| 2 | `bash reproduce/run.sh 2` | Bash and Docker on Linux/amd64 with working Landlock under Docker's default security profile. Allow about an hour based on the historical hosted run, plus initial image setup and downloads. Builds all four default publisher targets and runs the unmodified Comparator driver with nanoda enabled. |

| Tier | Expected final output line |
|---|---|
| 0 | `Offline checks passed. This run did not start Lean or Comparator.` |
| 1 | `Tier 1 passed. Evidence SHA-256 ad6acd7b7fbee926a4fa96fe61f50e8bcfa5e381d683317e8b8ea9a05c6437d9` |
| 2 | `Tier 2 passed. Evidence SHA-256 8d0ea4d8393b1f0768f5dbafeb3b8ec2f64c485fbf8e4c311d8f9cb9ca7ed2e6` |

| Expected evidence | Digest |
|---|---|
| Tier 0 [offline evidence index](checks/offline-evidence.json), SHA-256 | `b1d5e732dc2a80a2432c727f3b658f63be37651aa700596a4281397b641993f8` |
| Tier 0 publisher tree, Git SHA-1 | `b076b4b081298c4e909bac3f87f0e4462d1fb2cb` |
| Tier 1 canonical `review/tier1-evidence.json`, SHA-256 | `ad6acd7b7fbee926a4fa96fe61f50e8bcfa5e381d683317e8b8ea9a05c6437d9` |
| Tier 2 canonical `tier2-evidence.json`, SHA-256 | `8d0ea4d8393b1f0768f5dbafeb3b8ec2f64c485fbf8e4c311d8f9cb9ca7ed2e6` |
| Original Actions artifact ZIP, SHA-256 | `51c556d89448e6574e57dc4cceca799fd187d786fb7807516d65bc5629772307` |
| Original Actions job transcript after decompression, SHA-256 | `f4202727be9e16f795a32cf2e4df28be0917001edfb9102c821ba4ed81b57e21` |

The container fetches dependencies during image creation. The pinned project and verifier revisions are recorded in the [Lake manifest](primary/vp-vnp/lake-manifest.json), [toolchain file](primary/vp-vnp/lean-toolchain), [verifier lock](reproduce/versions.env) and [Dockerfile](Dockerfile). The base image and compiler installers are content-pinned. The Ubuntu package mirror supplies system utilities at build time. For Tiers 1–2, each verification runs in a new, unprivileged container with networking disabled and writes logs and evidence to a fresh `reproduction-results/` directory. A Linux host must support Landlock for Tier 2. An incompatible host fails the tier. Use a disposable Linux VM for an isolated proof replay.

Tier 1's evidence hashes all review Lean sources and checks 15 selected axiom readbacks against the historical receipts. Tier 2 verifies the exact publisher tree and driver, all dependency revisions, the five configured declarations, nanoda and Lean acceptance, and the driver's final success marker. The hashes cover canonical evidence JSON. Elapsed times, build job counts, log text and `.olean` bytes can vary with the host or build environment. The original GitHub job and comparable acceptance markers remain available in the [archival evidence](history/actions/README.md).

For an independent reproduction, record operator name or handle, permission to credit you, date in UTC, checkout commit, OS/kernel/architecture, Docker version, tiers completed, final lines, evidence hashes and any failures. Include logs or evidence JSON if shareable. A completed proof run and a human reading of statement correspondence are separate contributions. [Reproduction request](reconciliation/release-candidate.md).
