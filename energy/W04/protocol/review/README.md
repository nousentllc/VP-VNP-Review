# CRGC v0.3 reviewer evidence

This is a partial independent review of Work's W03 campaign, not a second complete campaign. The original `W03_Energy_Experiments.zip` and `W03_Results.pdf` are separate preserved inputs. Archive SHA-256: `39c6f5059905c05c7be6265622f7423ebf075f5f0b60e745023f90dbad1151e5`; PDF SHA-256: `2415ea56f41446b9e1320d1be2eed34002efa92c252d2d4a323b6c02aaea2012`. The prior integrated TeX SHA-256: `1c2f0b09f16b6833707d6d8e61ab4f48b8ceeb03e20bc9019aea82c99c175a9e`. All original files remain unchanged.

Extract W03 to a new directory. With Python, NumPy, SciPy and CasADi installed, run:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python audit_w03.py /path/to/Energy_Explorations/W03 --output fresh_audit.json --rerun-load
```

`audit_w03.py` checks all manifest files, trial denominator and reported target consistency, saved battery schedules, exact rational LP box bounds, AC solutions and corruption controls, and archived load trajectories. It imports Work's pure LP matrix assembly, exact box evaluator and AC checker; `highspy` is stubbed only when absent to import the solver-free parts of those modules. No HiGHS MIP solve is invoked in the archival battery review. The fixed-deadline comparisons are retrospective calculations from Work's recorded clocks. The optional E rerun uses Work's frozen forecasts and original policy implementation in the current Linux SciPy environment. `audit_w03.json` preserves the output, including all 72 fresh load trajectories, fixed-deadline comparisons and environment. `audit_run.log` records the console summary. `exact_controls.json` is the output of Work's `formal/replay_controls.py`; `formal_finite_checks.json` is the output of `finite_checks()` in `formal/verify.py` (imported without running Lean). These are finite checks, not a new Lean compilation. No independent UC reconstruction was run because Pyomo/HiGHS Python bindings were not installed; no full Lean toolchain was present. Work's same-machine replay remains its own recorded evidence.

Run the original packet's `src/verify_recorded.py` and `reproduce.py` with the pinned dependencies for broader replay. The earlier original Work v0.2 full companion package remains unavailable; the W03 archive recovers its W-E05 inputs and code. Preserve outputs separately and report platform differences, not only matching results.

`claims.csv` is the compact W03 admission register. The v0.3 master and prospective W04 protocol are separate deliverables. No W04 runs, field claims, national savings, or independent VP/VNP proof validation are established by this package.
