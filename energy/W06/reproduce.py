"""Verify release bytes and replay witnesses. Write new calculations outside this packet."""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
ROOT=Path(__file__).resolve().parent


def digest(path):
    from hashlib import sha256
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def integrity():
    manifest=ROOT/'SHA256SUMS.txt'
    checked=set()
    for line in manifest.read_text().splitlines():
        expected,rel=line.split('  ',1)
        p=(ROOT/rel).resolve()
        if ROOT not in p.parents or rel in checked or digest(p)!=expected:
            raise ValueError(rel)
        checked.add(rel)
    actual={p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*') if p.is_file()
            and '__pycache__' not in p.parts and p!=manifest}
    if checked!=actual:raise ValueError((actual-checked,checked-actual))
    print(f'Verified {len(checked)} release members.')
    return len(checked)


def audit(out,lean,packages):
    out=out.resolve()
    if out==ROOT or ROOT in out.parents:raise ValueError('Choose an output path outside W06')
    out.mkdir(parents=True,exist_ok=False);n=integrity()
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1')
    logs={}
    def run(label,script,*args):
        start=time.monotonic()
        p=subprocess.run([sys.executable,ROOT/script,*map(str,args)],env=env,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        (out/(label+'.log')).write_bytes(p.stdout)
        logs[label]={'seconds':time.monotonic()-start,'returncode':p.returncode}
        (out/'checks.json').write_text(json.dumps({'files':n,'steps':logs},indent=2)+'\n')
        if p.returncode:raise RuntimeError(f'{label} failed. See {out}/{label}.log')
    run('A','A/check.py','--data',ROOT/'A/results','--out',out/'A')
    run('B_exact','B/exact_controls.py')
    assert (out/'B_exact.log').read_bytes()==(ROOT/'B/results/exact_controls.json').read_bytes()
    run('B_stock','B/flat_review/check_data.py','--out',out/'B_stock.json.gz','--w05-zip',ROOT/'dependencies/W05_Energy_Experiments.zip')
    if lean:
        run('B_flat_lean','B/flat_review/verify_flat.py','--lean',lean,'--packages',packages,'--out',out/'B_flat_lean')
        run('B_lean','B/verify.py','--lean',lean,'--packages',packages,'--out',out/'B_lean','--replay-oleans')
    base=ROOT/'C'
    run('C_ac','C/ac.py','audit',base/'ac_results')
    run('C_uc','C/commitment.py','audit',base/'uc_results')
    run('C_clique','C/clique.py','audit',base/'ac_results',base/'exploratory/results')
    run('C_tree','C/uc_tree.py','audit',base/'uc_results',base/'exploratory/uc_results')
    run('C_physics','C/independent.py',base/'ac_results',base/'uc_results',out/'C_physics.json')
    assert json.loads((out/'C_physics.json').read_text())['uc']==json.loads((base/'diagnostics/independent.json').read_text())['uc']
    run('C_independent_rows','C/independent_review/review.py','--source',base,'--out',out/'independent_C')
    run('C_independent_lifts','C/independent_review/ac_lifts.py','--source',base,'--out',out/'independent_C')
    ep=out/'E'
    run('E','E/reproduce.py','audit','--out',ep)
    reserve=out/'E_reserve';shutil.copytree(ROOT/'E/reserve_activation_followup/results',reserve)
    run('E_reserve','E/reserve_activation_followup/check.py','--out',reserve)
    run('E_wear','E/wear_sensitivity/replay.py','--source',ROOT/'E','--out',out/'E_wear')
    assert (out/'E_wear/results.json').read_bytes()==(ROOT/'E/wear_sensitivity/results.json').read_bytes()
    original=json.loads((ROOT/'E/results/summary.json').read_text());replayed=json.loads((ep/'results/summary.json').read_text())
    assert original['tests']==replayed['tests']
    dep=ROOT/'dependencies';w05=dep/'W05_Energy_Experiments.zip'
    run('historical','E/historical/replay.py',w05,dep/'CRGC_W05_Independent_Opportunity_Review.zip',out/'historical.json')
    run('splices','E/historical/check_splice.py',w05,ROOT/'E/historical/splice.json.gz',out/'splice_audit.json')
    run('stock','E/historical/analytic_stock.py',w05,ROOT/'E/historical/splice.json.gz',out/'analytic_stock.json.gz')
    print('Archived witnesses replayed. New logs and wall times:',out)


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('action',choices=['integrity','audit']);ap.add_argument('--out',type=Path);ap.add_argument('--lean',type=Path);ap.add_argument('--packages',type=Path)
    a=ap.parse_args()
    if a.action=='audit':
        if not a.out or bool(a.lean)!=bool(a.packages):ap.error('audit needs --out; provide both Lean options together')
        audit(a.out,a.lean.resolve() if a.lean else None,a.packages.resolve() if a.packages else None)
    else:integrity()
