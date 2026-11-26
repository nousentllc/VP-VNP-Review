#!/usr/bin/env bash
set -euo pipefail
if [[ $# != 1 || ( $1 != 1 && $1 != 2 ) ]]; then
  echo 'Usage: bash reproduce/run.sh {1|2}' >&2
  exit 2
fi
cd "$(dirname "$0")/.."
command -v docker >/dev/null || { echo 'Docker is required for Tiers 1 and 2.' >&2; exit 1; }
tier=$1
image="vp-vnp-review:edition12-tier$tier"
mkdir -p reproduction-results
results=$(mktemp -d "reproduction-results/tier$tier.XXXXXX")
echo "Saving Tier $tier logs and evidence in $results"
docker build --platform linux/amd64 --target "tier$tier" --tag "$image" .
container=$(docker create --platform linux/amd64 --network none --cap-drop ALL \
  --security-opt no-new-privileges "$image")
trap 'docker rm -f "$container" >/dev/null' EXIT
status=0
docker start -a "$container" || status=$?
if [[ $(docker inspect --format '{{.State.ExitCode}}' "$container") != 0 ]]; then
  status=1
fi
docker cp "$container:/home/reproducer/results/." "$results/"
exit "$status"
