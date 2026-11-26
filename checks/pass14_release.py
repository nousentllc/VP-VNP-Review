"""Rebuild the complete publisher Lean project. External packages must be built at the locked revisions.

Use --offline to verify the archived evidence with Python alone.
"""
import argparse
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from graphlib import TopologicalSorter
import hashlib
import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory

from pass09_endpoint_replay import REVIEW, SOURCE, dependency_order, source_file
from pass12e_verify_pin import publisher_tree
from pass13_joint_replay import environment, imports, sha
from pass14_warnings import audit_modules

TARGETS = ["Statement", "Challenge", "Solution", "Paper"]
AXIOMS = "scripts.PrintAxioms"


def run(args, work):
    pin = json.loads((REVIEW / "source-lock.json").read_text())
    tree, count = publisher_tree(SOURCE)
    if (tree.hex(), count) != (pin["git_tree"], pin["blob_count"]):
        raise ValueError("Original publisher tree differs from lock")
    objects = work / "objects"
    objects.mkdir()
    env, revs = environment(args.mathlib.resolve(), objects)
    version = subprocess.check_output([args.lean, "--version"], env=env, text=True).strip()
    if f"version {pin['lean_toolchain'].split(':v')[-1]}," not in version:
        raise ValueError(version)
    cmd = [args.lean, "-j1", "-DautoImplicit=false"]
    config = json.loads((SOURCE / "comparator.json").read_text())
    declared = set().union(*(dependency_order(t) for t in TARGETS))
    modules = declared | {AXIOMS}
    if modules != {".".join(p.relative_to(SOURCE).with_suffix("").parts) for p in SOURCE.rglob("*.lean")}:
        raise ValueError("Source files and build targets differ")
    if "Challenge" in dependency_order("Solution"):
        raise ValueError("Solution imports the trusted challenge")
    def compile_one(name):
        rel = source_file(name)
        out = objects / rel.with_suffix(".olean")
        out.parent.mkdir(parents=True, exist_ok=True)
        p = subprocess.run([*cmd, "-o", str(out), str(rel)], cwd=SOURCE, env=env, capture_output=True, text=True)
        log = (p.stdout+p.stderr).strip()
        if p.returncode:
            raise RuntimeError(f"{name}: {p.returncode}\n{log}")
        item = dict(module=name, source=rel.as_posix(), sha256=sha(SOURCE/rel), exit_code=p.returncode)
        if log:
            item["output"] = log
        return item
    graph = TopologicalSorter({m:imports(m, modules) for m in sorted(modules)})
    graph.prepare()
    rows = {}
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        pending = {}
        while graph.is_active():
            for m in graph.get_ready():
                pending[pool.submit(compile_one,m)] = m
            done,_ = wait(pending,return_when=FIRST_COMPLETED)
            for job in done:
                m = pending.pop(job)
                rows[m] = job.result()
                graph.done(m)
                print(f"{len(rows)}/{len(modules)} {m}",flush=True)
    warning_audit = audit_modules(rows.values())
    names = config["theorem_names"]
    # Isolated environments prevent the challenge declarations from entering the proof imports.
    signatures = {}
    for target in ["Challenge", "Solution"]:
        query = work / (target+"Signatures.lean")
        query.write_text(f"import {target}\nset_option pp.all true\n"+"\n".join("#check @"+n for n in names)+"\n")
        signatures[target] = subprocess.check_output([*cmd,str(query)],env=env,cwd=SOURCE,text=True).strip()
    if signatures["Challenge"] != signatures["Solution"]:
        raise ValueError("Lean's fully printed challenge and solution signatures differ")
    query_file = REVIEW/"checks/pass14_release.lean"
    query = subprocess.run([*cmd,str(query_file)],env=env,cwd=SOURCE,capture_output=True,text=True,check=True)
    output = query.stdout+query.stderr
    import re
    axioms = {n:sorted(v.split(", ")) for n,v in re.findall(r"'([\w.]+)' depends on axioms: \[([^\]]+)\]",output)}
    if not set(names)<=axioms.keys() or any(set(a)-set(config["permitted_axioms"]) for a in axioms.values()):
        raise ValueError("Axiom readback failed: "+output)
    return dict(publisher_commit=pin["commit"],git_tree=tree.hex(),toolchain=version,
                external_checkout_revisions=revs,default_targets=TARGETS,
                default_target_modules=len(declared),modules_requested=len(modules),
                modules=[rows[m] for m in sorted(rows)],challenge_in_solution_imports=False,
                build_warning_audit=warning_audit, challenge_and_solution_signatures=signatures,
                matching_signature_sha256=hashlib.sha256(signatures["Solution"].encode()).hexdigest(),
                rate_olean_sha256=sha(objects / "Paper/Rate.olean"),
                verification=dict(query_file=query_file.relative_to(REVIEW).as_posix(),sha256=sha(query_file),
                                  exit_code=query.returncode,output=output,axioms=axioms),
                scope="All publisher .lean files compiled from source into empty project object path. Pinned external libraries used prebuilt. Single Lean kernel and isolated signature readbacks. Comparator has a separate receipt.")


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mathlib",required=True,type=Path)
    parser.add_argument("--lean",default="lean")
    parser.add_argument("--jobs",type=int,default=4)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--work-dir", type=Path, help="Previously absent directory in which to retain fresh objects for further readback")
    args=parser.parse_args()
    if args.jobs<1:parser.error("positive job count required")
    if args.work_dir is None:
        with TemporaryDirectory(prefix="vpvnp14-full-") as tmp:
            result=run(args,Path(tmp))
    else:
        args.work_dir.mkdir(exist_ok=False)
        result=run(args,args.work_dir.resolve())
    args.output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")


if __name__=="__main__":
    from offline_replays import run_entrypoint

    run_entrypoint(__file__, main)
