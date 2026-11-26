#!/usr/bin/env bash
set -euo pipefail
results=/home/reproducer/results
case "$1" in
  1)
    mkdir -p "$results"
    python3 ../../reproduce/tier1.py --targets > "$results/publisher-targets.txt"
    mapfile -t targets < "$results/publisher-targets.txt"
    lake build "${targets[@]}" 2>&1 | tee "$results/publisher-dependencies.log"
    python3 ../../reproduce/tier1.py --output "$results/review"
    ;;
  2)
    mkdir -p "$results"
    source ../../reproduce/versions.env
    python3 ../../reproduce/verify_tier2.py --inputs-only
    lake build 2>&1 | tee "$results/build.log"
    python3 ../../checks/pass14_warnings.py "$results/build.log"
    # Reuse the exact pinned driver while preventing Cargo from refreshing its registry.
    CARGO_NET_OFFLINE=true LOG_DIR="$results/comparator" \
      bash ../.github/scripts/comparator-check.sh 2>&1 | tee "$results/driver.log"
    python3 ../../reproduce/verify_tier2.py --results "$results"
    ;;
  *) exit 2 ;;
esac
