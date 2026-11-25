"""Check the post-hoc flat-tariff proof addendum against the pinned W06-B imports."""
import argparse
import gzip
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time

ROOT=Path(__file__).resolve().parent
sys.dont_write_bytecode=True
sys.path.insert(0, str(ROOT.parent))
from verify import ALLOWED, EXPECTED_COMPILER, read_pins, sha


def run(lean,packages,out):
    tic=time.perf_counter()
    if out.exists() and any(out.iterdir()):
        raise ValueError("Use a fresh output directory")
    out.mkdir(parents=True,exist_ok=True)
    lock=json.loads((ROOT/"lock.json").read_text())
    for rel,value in lock.items():
        assert sha(ROOT/rel)==value, rel
    version=subprocess.check_output([lean,"--version"],text=True)
    assert EXPECTED_COMPILER in version and "4.30.0-rc2" in version
    pins=read_pins(packages)
    clocks={}; exits={}
    with tempfile.TemporaryDirectory(prefix="crgc-flat-") as tmp:
        b=Path(tmp)
        env=dict(os.environ,LEAN_PATH=os.pathsep.join(str(p) for p in
                [b,*[packages/r["name"]/".lake/build/lib/lean" for r in pins]]))
        for m in ["FlatTariff","FlatAudit","FlatMutants","kernel_FlatTariff"]:
            start=time.perf_counter()
            if m.startswith("kernel_"):
                cmd=[lean.with_name("leanchecker"),"-v","FlatTariff"]
            else:
                src=ROOT/(m+".lean")
                shutil.copyfile(src,b/src.name)
                cmd=[lean,"-j1","-o",m+".olean",src.name]
            proc=subprocess.run(cmd,cwd=b,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
            (out/(m+".log")).write_text(proc.stdout)
            clocks[m]=time.perf_counter()-start;exits[m]=proc.returncode
            if m=="FlatMutants":
                intended=[i for i,s in enumerate(src.read_text().splitlines(),1) if s.startswith("example ")]
                actual=[int(v) for v in re.findall(r"FlatMutants\.lean:(\d+):\d+: error:",proc.stdout)]
                assert proc.returncode and intended==actual
            else:
                assert proc.returncode==0 and "warning:" not in proc.stdout,m
                if m.startswith("kernel_"):
                    assert "replaying FlatTariff" in proc.stdout
        audit=(out/"FlatAudit.log").read_text()
        axioms={n:[t.strip() for t in names.split(",")] for n,names in
                re.findall(r"'([^']+)' depends on axioms: \[([^\]]*)\]",audit)}
        axioms.update({n:[] for n in re.findall(r"'([^']+)' does not depend on any axioms",audit)})
        names=set(re.findall(r"^theorem (\w+)",(ROOT/"FlatTariff.lean").read_text(),re.M))
        assert set(axioms)=={"W06.Flat."+n for n in names} and all(set(row)<=ALLOWED for row in axioms.values())
        start=time.perf_counter()
        subprocess.run([sys.executable,ROOT/"check_data.py","--out",b/"replay.json.gz"],check=True)
        clocks["data_replay"]=time.perf_counter()-start
        assert gzip.decompress((b/"replay.json.gz").read_bytes()) == gzip.decompress((ROOT/"data_check.json.gz").read_bytes())
    output={"version":version.strip(),"lean_sha256":sha(lean),"pins":{p["name"]:p["rev"] for p in pins},
            "exit":exits,"axioms":axioms,"rejected_lines":actual,"same_kernel_module_replay":True,
            "archived_numeric_output_sha256":sha(ROOT/"data_check.json.gz"),
            "replay_comparison":"Exact uncompressed JSON bytes; gzip container metadata may vary across Python versions."}
    (out/"audit.json").write_text(json.dumps(output,sort_keys=True,indent=2)+"\n")
    clocks["total"]=time.perf_counter()-tic
    (out/"seconds.json").write_text(json.dumps(clocks,indent=2)+"\n")
    print("Flat addendum:",len(axioms),"declarations and",len(actual),"negative controls")


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    for arg in ["--lean","--packages","--out"]:
        p.add_argument(arg,type=Path,required=True)
    a=p.parse_args()
    run(a.lean.resolve(),a.packages.resolve(),a.out.resolve())
