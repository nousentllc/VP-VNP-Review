"""Build all W06-B sources and check the enumerated axioms and exact negative controls."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time


ROOT = Path(__file__).resolve().parent
FORMAL = ROOT / "formal"
MODULES = ("COA", "BoxDual", "Tests", "Closing", "Inventory")
ALLOWED = {"propext", "Classical.choice", "Quot.sound"}
EXPECTED_COMPILER = "3dc1a088b6d2d8eafe25a7cd7ec7b58d731bd7cc"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_pins(packages):
    rows = json.loads((FORMAL / "lake-manifest.json").read_text())["packages"]
    for package in rows:
        folder = packages / package["name"]
        actual = subprocess.check_output(["git", "-C", folder, "rev-parse", "HEAD"], text=True)
        changes = subprocess.check_output(["git", "-C", folder, "status", "--porcelain",
                                           "--untracked-files=no"], text=True)
        if actual.strip() != package["rev"] or changes.strip():
            raise ValueError(f"Source checkout differs from lock for {package['name']}")
    return rows


def read_axioms(stdout):
    seen = {name: [w.strip() for w in refs.split(",") if w.strip()]
            for name, refs in re.findall(r"'([^']+)' depends on axioms: \[([^\]]*)\]", stdout)}
    seen.update({n: [] for n in re.findall(r"'([^']+)' does not depend on any axioms", stdout)})
    expected = set()
    for module, namespace in (("COA", "W06"), ("BoxDual", "W06.Dual"), ("Tests", "W06.Tests"), ("Closing", "W06.Closing")):
        names = re.findall(r"^theorem (\w+)", (FORMAL / (module + ".lean")).read_text(), re.M)
        expected.update(f"{namespace}.{name}" for name in names)
    if set(seen) != expected or any(set(refs) - ALLOWED for refs in seen.values()):
        raise ValueError("The axiom inventory differs from the positive source declarations")
    return seen


def check(lean, packages, out, replay_oleans):
    start = time.perf_counter()
    if out.exists() and any(out.iterdir()):
        raise ValueError("Use a fresh results directory")
    out.mkdir(parents=True, exist_ok=True)
    lean = lean.resolve()
    version = subprocess.check_output([lean, "--version"], text=True).strip()
    if "version 4.30.0-rc2" not in version or EXPECTED_COMPILER not in version:
        raise ValueError(version)
    pins = read_pins(packages)
    inputs = json.loads((ROOT / "proof_lock.json").read_text())
    for rel, digest in inputs["sha256"].items():
        if sha(ROOT / rel) != digest:
            raise ValueError(f"Source differs from published pin: {rel}")
    result = {"lean": version, "lean_binary_sha256": sha(lean),
              "pins_verified": {row["name"]: row["rev"] for row in pins},
              "object_dependencies": "Prebuilt and trusted. Tracked checkout sources matched pins.",
              "packages_with_prebuilt_lean_dir": [row["name"] for row in pins
                  if (packages / row["name"] / ".lake/build/lib/lean").is_dir()],
              "compile_exit": {}, "kernel_replay": {}}
    times = {}
    with tempfile.TemporaryDirectory(prefix="crgc-w06b-") as tmp:
        build = Path(tmp)
        paths = [build, *(packages / row["name"] / ".lake/build/lib/lean" for row in pins)]
        env = dict(os.environ, LEAN_PATH=os.pathsep.join(map(str, paths)))
        for module in (*MODULES, "FalseVariants"):
            src = FORMAL / (module + ".lean")
            shutil.copyfile(src, build / src.name)
            options = ["-j1"] if module == "FalseVariants" else ["-j1", "-o", module+".olean"]
            begin = time.perf_counter()
            proc = subprocess.run([lean, *options, src.name], cwd=build, env=env,
                                  text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            times[module] = time.perf_counter()-begin
            (out / (module + ".log")).write_text(proc.stdout)
            result["compile_exit"][module] = proc.returncode
            if module == "FalseVariants":
                actual = [int(n) for n in re.findall(r"FalseVariants\.lean:(\d+):\d+: error:", proc.stdout)]
                wanted = [i for i,line in enumerate(src.read_text().splitlines(),1) if line.startswith("example")]
                if actual != wanted or proc.returncode == 0:
                    raise ValueError(f"Unexpected negative-control diagnostics: {actual}")
                result["rejected_false_variants"] = actual
            elif proc.returncode or "warning:" in proc.stdout:
                raise RuntimeError(f"See {module}.log")
        if replay_oleans:
            binary = lean.with_name("leanchecker")
            for module in MODULES[:-1]:
                begin = time.perf_counter()
                proc = subprocess.run([binary, "-v", module], cwd=build, env=env, text=True,
                                      stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=240)
                times["kernel_"+module] = time.perf_counter()-begin
                (out / ("kernel_"+module+".log")).write_text(proc.stdout)
                if proc.returncode or ("replaying "+module) not in proc.stdout:
                    raise RuntimeError(f"Unexpected leanchecker result for {module}")
                result["kernel_replay"][module] = proc.returncode
    log = (out / "Inventory.log").read_text()
    result["axioms"] = read_axioms(log)
    result["inspected_declarations"] = len(result["axioms"])
    result["declaration_dependency_records"] = len(re.findall(r"LOCAL-EDGES ", log))
    exact = subprocess.check_output([sys.executable, ROOT / "exact_controls.py"])
    if exact != (ROOT / "results/exact_controls.json").read_bytes():
        raise ValueError("Rational controls differ from the archived record")
    result["exact_controls_sha256"] = hashlib.sha256(exact).hexdigest()
    (out / "proof_audit.json").write_text(json.dumps(result, indent=2, sort_keys=True)+"\n")
    times["elapsed_including_preflight_and_controls"] = time.perf_counter()-start
    (out / "wall_seconds.json").write_text(json.dumps(times,indent=2)+"\n")
    print("Audited", result["inspected_declarations"], "declarations and", len(result["rejected_false_variants"]), "mutants")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lean", type=Path, required=True)
    parser.add_argument("--packages", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--replay-oleans", action="store_true", help="Recheck local module declarations using the distributed Lean kernel")
    args = parser.parse_args()
    check(args.lean, args.packages.resolve(), args.out.resolve(), args.replay_oleans)
