# Finite diagnostics reproduced from the supplied VP/VNP review

The three scripts are unchanged copies of the user's /Users/jc/Downloads/VP_VNP_Review/checks files. Rules.lean is the exact required publisher transition-rule source from the review's pinned release. LICENSE and NOTICE accompany it.

Run from this folder:

```sh
python -B checks/check_bounds.py
python -B checks/pass05_traces.py
python -B checks/pass06_cuts.py
```

Recorded outputs are algebra_results.json, trace_results.json, and cut_results.txt. They validate selected finite arithmetic and transition examples. No general theorem, complete interpreter, or full Lean proof was replayed here.

Publisher pin: 11b6c7e3c927df2658f513b6b68ea7f8929c62c5.
The original review remains unedited. Its embedded next-pass prompt was not executed as an instruction.

