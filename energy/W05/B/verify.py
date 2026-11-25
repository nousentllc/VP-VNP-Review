"""Build the source against locked prebuilt dependencies and audit the proof statements."""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FORMAL = ROOT / "formal"
MODULES = ["AIPC", "Anchor", "Transfer", "Terminal", "Obstructions", "Inventory"]
ALLOWED = {"propext", "Classical.choice", "Quot.sound"}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def package_lock(packages):
    expected = json.loads((FORMAL/"lake-manifest.json").read_text())["packages"]
    records = []
    for row in expected:
        directory = packages/row["name"]
        rev = subprocess.check_output(["git","-C",str(directory),"rev-parse","HEAD"],text=True).strip()
        changes = subprocess.check_output(["git","-C",str(directory),"status","--porcelain",
                                           "--untracked-files=no"],text=True).strip()
        if rev!=row["rev"] or changes:
            raise ValueError(f"{row['name']} checkout differs from locked source")
        records.append({"name":row["name"],"commit":rev,"tracked_sources_clean":True})
    return records


def verify(lean, packages, out):
    if out.exists() and any(out.iterdir()):
        raise ValueError("Select a fresh output directory.")
    out.mkdir(parents=True,exist_ok=True)
    version=subprocess.check_output([str(lean),"--version"],text=True).strip()
    if "version 4.30.0-rc2" not in version:
        raise ValueError(version)
    inputs=json.loads((ROOT/"proof_lock.json").read_text())
    for name,digest in inputs["sha256"].items():
        if sha(ROOT/name)!=digest:
            raise ValueError(f"Source differs from W05-B proof lock: {name}")
    locks=package_lock(packages)
    results={"lean":version,"lean_binary_sha256":sha(lean),"lock":locks,"source_modules":{},
             "dependencies":"Prebuilt Lean/mathlib transitive object files. Source revisions and tracked worktrees checked."}
    with tempfile.TemporaryDirectory(prefix="crgc-w05b-") as tmp:
        target=Path(tmp)
        env=dict(os.environ, LEAN_PATH=os.pathsep.join(map(str,
            [target,*[packages/p["name"]/".lake/build/lib/lean" for p in locks]])))
        for module in [*MODULES,"FalseVariants"]:
            src=FORMAL/(module+".lean")
            shutil.copyfile(src,target/src.name)
            options=["-j1"] if module=="FalseVariants" else ["-j1","-o",module+".olean"]
            proc=subprocess.run([str(lean),*options,src.name],cwd=target,env=env,text=True,
                                stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
            (out/(module+".log")).write_text(proc.stdout)
            results["source_modules"][module]={"source_sha256":sha(src),"exit":proc.returncode}
            if module!="FalseVariants" and (proc.returncode or "declaration uses 'sorry'" in proc.stdout):
                raise ValueError(f"{module} failed source validation")
            if module=="FalseVariants":
                expected_lines=[i for i,l in enumerate(src.read_text().splitlines(),1) if l.startswith("example")]
                errors=[int(i) for i in re.findall(r"FalseVariants\.lean:(\d+):\d+: error:",proc.stdout)]
                if proc.returncode==0 or errors!=expected_lines:
                    raise ValueError(f"Negative controls had unexpected outputs: {errors} versus {expected_lines}")
                results["false_variants_rejected"]=len(errors)
                results["false_variant_lines"]=errors
    log=(out/"Inventory.log").read_text()
    axioms={n:[a.strip() for a in vals.split(",") if a.strip()]
            for n,vals in re.findall(r"'([^']+)' depends on axioms: \[([^\]]*)\]",log)}
    axioms.update({n:[] for n in re.findall(r"'([^']+)' does not depend on any axioms",log)})
    expected={n for n in re.findall(r"^#print axioms (\S+)$",(FORMAL/"Inventory.lean").read_text(),re.M)}
    if set(axioms)!=expected or any(set(row)-ALLOWED for row in axioms.values()):
        raise ValueError("Missing theorem inspection or axiom outside the stated scope")
    results["transitive_axioms"]=axioms
    results["inspected_declarations"]=len(axioms)
    results["local_dependency_edges_reported"]=len(re.findall("LOCAL-EDGES ",log))
    evidence=subprocess.check_output([sys.executable,str(ROOT/"exact_controls.py")],text=True)
    (out/"exact_controls.json").write_text(evidence)
    (out/"proof_audit.json").write_text(json.dumps(results,indent=2,sort_keys=True)+"\n")


if __name__=="__main__":
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--lean",required=True,type=Path)
    ap.add_argument("--packages",required=True,type=Path)
    ap.add_argument("--out",required=True,type=Path)
    args=ap.parse_args()
    verify(args.lean.resolve(),args.packages.resolve(),args.out.resolve())
