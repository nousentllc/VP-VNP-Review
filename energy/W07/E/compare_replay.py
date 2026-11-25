"""Compare every deterministic fresh primary input, outcome and certificate after a clean execution."""
import hashlib
import json
import sys
from pathlib import Path


def compare(source,fresh):
    paths=sorted(f.relative_to(fresh) for f in fresh.rglob('*') if f.is_file())
    variable={'independent.json','timing.json'}
    files=0;nbytes=0
    for rel in paths:
        a=source/rel;b=fresh/rel
        if str(rel)=='independent.json':
            va=json.loads(a.read_text());vb=json.loads(b.read_text())
            va.pop('seconds');vb.pop('seconds');assert va==vb;continue
        if str(rel) in variable:continue
        if str(rel)=="summary.json":
            assert json.loads(a.read_text())==json.loads(b.read_text());continue
        assert a.read_bytes()==b.read_bytes(),str(rel)
        files+=1;nbytes+=b.stat().st_size
    required=set(source.glob('certificates/*.gz'))|set(source.glob('outcomes/*.gz'))|set(source.glob('inputs/*.gz'))
    assert all((fresh/f.relative_to(source)).exists() for f in required)
    return dict(byte_identical_deterministic_files=files,deterministic_bytes=nbytes,
                certificates=sum(1 for _ in fresh.glob('certificates/*.gz')),policy_trajectory_files=sum(1 for _ in fresh.glob('outcomes/*.gz')),
                frozen_cases=sum(1 for _ in fresh.glob('inputs/*.gz')),summary_all_fields_structurally_identical=True, audit_counts_equal_excluding_elapsed_time=True)
if __name__=='__main__':
    val=compare(Path(sys.argv[1]),Path(sys.argv[2]));Path(sys.argv[3]).write_text(json.dumps(val,indent=2)+'\n')
