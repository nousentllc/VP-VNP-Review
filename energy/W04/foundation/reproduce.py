"""Replay W03 in a fresh directory. All operational parameters live in protocol/."""
import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent


def run():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output',required=True,type=Path)
    ap.add_argument('--experiments',nargs='+',choices=list('ABCDE'),default=list('ABCDE'))
    ap.add_argument('--lean-packages',type=Path,help='Optional existing mathlib package cache at the pinned revision')
    ap.add_argument('--lean',default='lean')
    ap.add_argument('--retune',action='store_true',help='Rerun A development timing instead of using the frozen selection')
    args=ap.parse_args()
    out=args.output.resolve()
    if out==ROOT/'results' or (out.exists() and any(out.iterdir())):
        ap.error('Choose a new or empty output directory to preserve the original measurements.')
    out.mkdir(parents=True,exist_ok=True)
    env={**os.environ,'W03_RESULTS':str(out),'PYTHONDONTWRITEBYTECODE':'1',
         'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1','VECLIB_MAXIMUM_THREADS':'1'}
    def invoke(script,*cmd):
        subprocess.run([sys.executable,str(ROOT/script),*map(str,cmd)],env=env,check=True,cwd=ROOT)
    if 'A' in args.experiments:
        (out/'A').mkdir()
        if args.retune:invoke('src/battery.py','development')
        else:
            decision=json.loads((ROOT/'protocol/freeze.json').read_text())['selected_presolve']
            (out/'A/development.json').write_text(json.dumps({'selected':decision,'source':'archived frozen selection'}))
        invoke('src/battery.py','holdout');invoke('src/battery_audit.py')
    if 'B' in args.experiments:
        extra=['--packages',args.lean_packages.resolve(),'--lean',args.lean] if args.lean_packages else []
        invoke('formal/verify.py','--out',out/'B',*extra)
    if 'C' in args.experiments:invoke('src/ac.py')
    if 'D' in args.experiments:invoke('src/uc.py')
    if 'E' in args.experiments:invoke('src/load_control.py','run')
    if set(args.experiments)==set('ABCDE'):invoke('src/summarize.py')
    print(f'Replay saved in {out}')


if __name__=='__main__':run()
