"""Replay archive evidence without writing to the archive. Supports independent tracks."""
import argparse
import csv
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
ROOT=Path(__file__).resolve().parent

def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(gzip.decompress(p.read_bytes()) if p.suffix=='.gz' else p.read_bytes())
def audit_manifest():
    manifest=ROOT/'SHA256SUMS.txt'
    entries={}
    for line in manifest.read_text().splitlines():
        h,key=line.split('  ',1)
        assert key not in entries and not Path(key).is_absolute() and '..' not in Path(key).parts
        entries[key]=h
    actual={p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*') if p.is_file() and p!=manifest}
    assert set(entries)==actual
    for k,h in entries.items():assert digest(ROOT/k)==h,k
    return len(entries)
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('out',type=Path);parser.add_argument('--track',choices=['all','A','B','C','E','master'],default='all')
    parser.add_argument('--lean',type=Path);parser.add_argument('--packages',type=Path)
    parser.add_argument('--fresh',action='store_true',help='Also regenerate fresh A and E panels and historical E results.')
    args=parser.parse_args()
    o=args.out.resolve();assert not o.is_relative_to(ROOT)
    o.mkdir(parents=True,exist_ok=True);assert not any(o.iterdir()),o
    elapsed=time.perf_counter();count=audit_manifest();steps={}
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONHASHSEED='902',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1')
    def step(name,cmd,cwd=ROOT,exact=None):
        start=time.perf_counter()
        with (o/(name+'.log')).open('wb') as log, (o/(name+'.stderr')).open('wb') as err:
            res=subprocess.run([sys.executable,'-B',*map(str,cmd)],cwd=cwd,env=env,stderr=err,stdout=log)
        steps[name]=dict(returncode=res.returncode,seconds=time.perf_counter()-start)
        (o/'steps.json').write_text(json.dumps(steps,indent=2)+'\n')
        if res.returncode:raise RuntimeError(f'{name} failed, inspect log and stderr')
        if exact:assert json.loads((o/(name+'.log')).read_bytes())==read(exact),name
    def active(k):return args.track in ['all',k]
    if active('master'):
        dest=o/'master';dest.mkdir()
        for f in ['source_page.json','export.py']:shutil.copy2(ROOT/'manuscript'/f,dest/f)
        step('master_export',[dest/'export.py'])
        for f in ['CRGC_Whitepaper_v0.6.tex','source_order.json']:assert (dest/f).read_bytes()==(ROOT/'manuscript'/f).read_bytes()
        statuses=list(csv.DictReader((ROOT/'protocol/W06_Adjudication.csv').open()))
        tex=(dest/'CRGC_Whitepaper_v0.6.tex').read_text()
        assert len(statuses)==52 and all(f"{r['id']} & {r['verdict']} &" in tex for r in statuses)
    if active('B'):
        step('B_controls',['B/exact_controls.py'],exact=ROOT/'B/results/exact_controls.json')
        for label,p in [('A','A/results/records.json'),('E','E/results/kernels.json.gz')]:
            step('B_correspondence_'+label,['B/correspondence.py',label,p],exact=ROOT/f'B/results/engineering-{label}.json')
        if args.lean or args.packages:
            assert args.lean and args.packages
            tool=['--lean',args.lean.resolve(),'--packages',args.packages.resolve()]
            step('B_lean',['B/verify.py',*tool,'--out',o/'lean','--replay-oleans'])
            step('B_real',['B/addendum/verify_addendum.py',*tool,'--out',o/'infimum'])
            assert read(o/'lean/proof_audit.json')==read(ROOT/'B/results/lean/proof_audit.json')
            assert read(o/'infimum/audit.json')['axioms']==read(ROOT/'B/results/infimum/audit.json')['axioms']
    if active('A'):
        step('A_verify',['A/verify.py'])
        step('A_strong_baseline',['A/audit_baseline.py'],exact=ROOT/'A/results/baseline_supplement.json')
        step('A_regression',['A/regression/w06_check.py','--data','A/regression/input','--out',o/'a_regression'])
        if args.fresh:
            dest=o/'fresh_A';step('A_fresh',['A/run.py','holdout',dest]);step('A_fresh_verify',['A/verify.py',dest])
            def cases(p):return [{k:v for k,v in r.items() if k not in ['direct_s','staged_s','milp_s']} for r in csv.DictReader(p.open())]
            assert cases(dest/'families.csv')==cases(ROOT/'A/results/families.csv')
    if active('E'):
        dest=o/'e_stored';cal=o/'calendar'
        shutil.copytree(ROOT/'E/results',dest);shutil.copytree(ROOT/'E/calendar_relaxation/results',cal)
        step('E_verify',['E/independent.py',dest]);step('E_policy',['E/policy_audit.py',dest,o/'issued_policy.json'])
        step('E_calendar',['E/calendar_relaxation/check.py',dest,cal])
        assert read(cal/'check.json')['panels']==read(ROOT/'E/calendar_relaxation/results/check.json')['panels']
        step('E_forward',['review_checks/forward_e.py'],exact=ROOT/'review_checks/forward_e.json')
        if args.fresh:
            ed=o/'fresh_E';step('E_historical',['E/regression.py',o/'e_history'])
            step('E_freeze',['E/run.py','freeze',ed])
            assert (ed/'inputs.sha256').read_bytes()==(ROOT/'E/results/inputs.sha256').read_bytes()
            step('E_fresh',['E/run.py','run',ed]);step('E_cost',['E/summarize.py',ed])
            step('E_compare',['E/compare_replay.py','E/results',ed,o/'e_match.json'])
            step('E_fresh_calendar',['E/calendar_relaxation/run.py',ed,o/'calendar_fresh'])
            step('E_fresh_calendar_verify',['E/calendar_relaxation/check.py',ed,o/'calendar_fresh'])
            assert read(o/'calendar_fresh/check.json')['panels']==read(cal/'check.json')['panels']
    if active('C'):
        step('C_certificates',['C/verify.py',o/'C','--w06'])
        step('C_longer_witness',['C/direct_followup.py','check'])
        step('C_official_longer_rows',['C/audit_direct_original.py'],exact=ROOT/'C/postfreeze/direct_uc/independent_rows.json')
    report=dict(manifest_entries=count,stage=args.track,fresh_A_E=args.fresh,lean_rebuild='B_lean' in steps,
                elapsed_s=time.perf_counter()-elapsed,steps=steps)
    (o/'audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Verified',count,'files;',len(steps),'completed checks. See',o/'audit.json')
if __name__=='__main__':main()
