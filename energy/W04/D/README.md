# W04-D replication

Run from the W04 root, using the same single-thread environment as the main README. New output directories keep each trial's raw log, vectors and checkpoints.

    python D/panel.py /tmp/crgc-d-primary/raw
    python D/check.py /tmp/crgc-d-primary/raw /tmp/crgc-d-primary/analysis
    python D/analyze.py /tmp/crgc-d-primary/raw /tmp/crgc-d-primary/analysis
    python D/serial_replay.py /tmp/crgc-d-serial/raw
    python D/check.py /tmp/crgc-d-serial/raw /tmp/crgc-d-serial/analysis
    python D/analyze.py /tmp/crgc-d-serial/raw /tmp/crgc-d-serial/analysis

The primary panel uses two concurrent single-thread UC workers. The secondary whole-panel sensitivity uses one UC worker and a longer Python import allowance. Details and the reason for this change appear in replay_decision.md. Do not pool these panels. Original dimensions, stage clocks and incumbent/bound events appear in record.json where the worker reached its first checkpoint. supervisor.json exists for every attempted cell. Integer schedules in .npz align to columns.json.gz by name. A run without a witnessed feasible plan has no available fallback. Absolute dollar objectives pertain to the individual truncated model. The tied restricted MILP's objective bound applies only to that restricted subproblem. The primary and replay analyses use only outer-LP and unrestricted MILP bounds for the full-model target.
