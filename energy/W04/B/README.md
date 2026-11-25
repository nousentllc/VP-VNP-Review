# Replaying W04-B

Run from W04. Keep its sibling foundation/formal directory beside B. Python 3.9 or newer suffices for the rational controls and driver. The replay requires the Lean executable matching foundation/formal/lean-toolchain and its exact mathlib package lock. Set LEAN_BIN to its full executable path and PACKAGES to a Lake package directory with the locked Git checkouts and compiled dependency artifacts.

    python3 B/exact_controls.py
    python3 B/environment.py --lean "$LEAN_BIN" --packages "$PACKAGES"
    python3 B/verify.py --lean "$LEAN_BIN" --packages "$PACKAGES" --out /tmp/w04b-replay

On a fresh machine with elan, Git, network access and a disposable copy of the packet, copy foundation/formal to a temporary bootstrap directory first. Run these commands from that copy, then return to the original W04 packet.

    lake update
    lake exe cache get
    LEAN_BIN="$(elan which lean)"
    PACKAGES="$PWD/.lake/packages"
    cd "$W04_PACKET"
    python3 B/verify.py --lean "$LEAN_BIN" --packages "$PACKAGES" --out /tmp/w04b-replay

Set W04_PACKET to the absolute path to the original W04 packet before running the bootstrap commands. The replay verifies revisions against the original lock and rejects changes to that lock or the historical Lean source. For a fresh cache, run lake update in a disposable directory and check that its resolved revisions match the original lock before accepting the replay. This campaign used a prebuilt dependency cache. The cold network bootstrap is supplied for portability and was not itself run. The release compiler and cached object provenance belong to the trusted base. The recorded transitive axiom set and statement signatures are in results/Inventory.log. Inventory.log contains actual theorem signatures, transitive axioms, and dependency edges among 100 local declarations including compiler-generated helpers. The Git lock identifies package source revisions. It does not rebuild Lean, mathlib or every imported object from source. To reproduce only new checks after running the historical controls, add --skip-w03. Each default replay builds the named user modules from source in a temporary directory.
