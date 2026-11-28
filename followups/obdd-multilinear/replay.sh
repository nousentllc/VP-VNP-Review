#!/usr/bin/env bash
# Check both source files using an existing Mathlib build or this package's Lake environment.
set -euo pipefail
cd "$(dirname "$0")"
run_dir=$(mktemp -d)
trap 'rm -rf "$run_dir"' EXIT
lean_bin=${LEAN_BIN:-lean}
if [[ -n ${MATHLIB_DIR:-} ]]; then
    mathlib=$(cd "$MATHLIB_DIR" && pwd)
    if [[ -f "$mathlib/.git/HEAD" || -f "$mathlib/.git" ]]; then
        test "$(git -C "$mathlib" rev-parse HEAD)" = 0df444a360eaa60ab8c11dca51a86af692955474
    fi
    paths="$mathlib/.lake/build/lib/lean"
    for pkg in "$mathlib"/.lake/packages/*; do
        paths="$paths:$pkg/.lake/build/lib/lean"
    done
else
    paths=$(lake env printenv LEAN_PATH)
fi
export LEAN_PATH="$run_dir:$paths"
version=$("$lean_bin" --version)
echo "$version"
[[ "$version" == *'version 4.33.1,'* && "$version" == *819816b2e0a3bf405af45ae5c7af2491d8f5bee6* ]]
"$lean_bin" -DwarningAsError=true -o "$run_dir/SharedOBDD.olean" SharedOBDD.lean
echo "Compiler and polynomial specification accepted."
"$lean_bin" -DwarningAsError=true -o "$run_dir/Controls.olean" Controls.lean
echo "Sharing, Boolean truth table, off-cube arithmetic, terminal and invalid-input controls accepted."

# A changed opcode preserves the register layout and the 3s length. Verify that the
# semantic proof, specifically, rejects the resulting program.
python3 - "$run_dir" <<'PY'
from pathlib import Path
import sys

source = Path("SharedOBDD.lean").read_text()
original = "⟨.mul, .input q.var, .gate 0⟩"
assert source.count(original) == 1
directory = Path(sys.argv[1]) / "mutation"
directory.mkdir()
(directory / "SharedOBDD.lean").write_text(source.replace(original, original.replace(".mul", ".add")))
PY
if "$lean_bin" --root="$run_dir/mutation" "$run_dir/mutation/SharedOBDD.lean" > "$run_dir/mutation.log" 2>&1; then
    echo "Unexpected acceptance of the changed opcode." >&2
    exit 1
fi
python3 - "$run_dir/mutation.log" <<'PY'
from pathlib import Path
import re
import sys

lines = Path("SharedOBDD.lean").read_text().splitlines()
start = next(i for i, line in enumerate(lines, 1) if line.startswith("theorem compile_slots"))
end = next(i for i, line in enumerate(lines, 1) if line.startswith("open MvPolynomial"))
log = Path(sys.argv[1]).read_text()
errors = re.findall(r"SharedOBDD\.lean:(\d+):\d+: error: ([^\n]*)", log)
if not errors or not all(start <= int(row) < end and "unsolved goals" in msg for row, msg in errors):
    raise SystemExit("Unexpected rejection reason:\n" + log)
print("Changed multiplication to addition: the compiler semantics proof rejected the mutation.")
PY
