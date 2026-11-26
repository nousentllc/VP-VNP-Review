#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/versions.env"
toolchain=$(tr -d '[:space:]' < lean-toolchain)

checkout() {
  local url=$1 path=$2 commit=$3
  git init -q "$path"
  git -C "$path" remote add origin "$url"
  git -C "$path" fetch -q --depth 1 origin "$commit"
  git -C "$path" checkout -q --detach FETCH_HEAD
  test "$(git -C "$path" rev-parse HEAD)" = "$commit"
}

mkdir -p "$TOOLS_DIR/bin"
checkout https://github.com/leanprover/comparator.git "$TOOLS_DIR/comparator" "$COMPARATOR_COMMIT"
(cd "$TOOLS_DIR/comparator" && lake build comparator)
checkout https://github.com/leanprover/lean4export.git "$TOOLS_DIR/lean4export" "$LEAN4EXPORT_COMMIT"
(cd "$TOOLS_DIR/lean4export" && lake "+$toolchain" build lean4export)
checkout https://github.com/robsimmons/nanoda_lib.git "$TOOLS_DIR/nanoda" "$NANODA_COMMIT"
cargo build --release --locked --manifest-path "$TOOLS_DIR/nanoda/Cargo.toml"
GOBIN="$TOOLS_DIR/bin" CGO_ENABLED=0 go install "github.com/zouuup/landrun/cmd/landrun@$LANDRUN_COMMIT"
printf '%s\n' "$LANDRUN_COMMIT" > "$TOOLS_DIR/bin/landrun.commit"
