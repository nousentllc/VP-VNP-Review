"""Read-only certificate replay for W07-C. Use --w06 for prior regression."""
import argparse
import contextlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path
from fractions import Fraction as F
ROOT=Path(__file__).resolve().parent
def external(src,name):
    s=importlib.util.spec_from_file_location(name,src);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def run(out,with_regression):
    import ac,clique,commitment,uc_tree
    import check_lock,coverage,feasible_gains,tree_coverage
    from pyomo.common.numeric_types import RegisterNumericType
    RegisterNumericType(F)
    check_lock.main();out.mkdir(parents=True,exist_ok=True)
    begin=time.perf_counter();times={};checks=[]
    def step(key,fn):
        start=time.perf_counter();v=fn();times[key]=time.perf_counter()-start;return v
    for p in sorted((ROOT/'inputs').glob('*.m')):
        d=ROOT/'ac_results'/p.stem
        step('primary_'+p.stem,lambda:ac.audit(p,d))
        for label,extra in [('registered',ROOT/'exploratory/results'/p.stem),('diagnostic',ROOT/'postfreeze'/p.stem)]:
            if extra.exists():step(label+'_'+p.stem,lambda:clique.audit(p,d,extra))
    for p in sorted((ROOT/'inputs').glob('20*.json')):
        for t in [24,48]:
            d=ROOT/'uc_results'/f'{p.stem}_{t}'
            step('primary_'+d.name,lambda:commitment.audit(p,t,d))
            branch=ROOT/'exploratory/uc_results'/d.name
            if branch.exists():step('registered_'+d.name,lambda:uc_tree.audit(p,t,d,branch))
    for script,key in [('coverage.py','coverage'),('tree_coverage.py','trees'),('feasible_gains.py','feasible_gains')]:
        actual=step(key,lambda:subprocess.check_output([sys.executable,'-B',ROOT/script],cwd=ROOT))
        assert json.loads(actual)==json.loads((ROOT/'postfreeze'/(key+'.json')).read_bytes())
    physics=out/'physics.json'
    step('physical',lambda:subprocess.run([sys.executable,'-B',ROOT/'independent.py',ROOT/'ac_results',ROOT/'uc_results',physics],check=True))
    assert json.loads(physics.read_bytes())==json.loads((ROOT/'postfreeze/physics.json').read_bytes())
    for script,receipt in [('review.py','receipt.json'),('ac_lifts.py','ac_lifts.json')]:
        step(script,lambda:subprocess.run([sys.executable,'-B',ROOT/'independent_review'/script,'--source',ROOT,'--out',out],check=True))
        assert json.loads((out/receipt).read_bytes())==json.loads((ROOT/'independent_review'/receipt).read_bytes())
    if with_regression:
        with tempfile.TemporaryDirectory() as temp:
            with zipfile.ZipFile(ROOT/'regression/W06_C_Regression.zip') as z:z.extractall(temp)
            base=Path(temp)/'C'
            for name,cmd in [('historical_ac',['ac.py','audit','ac_results']),('historical_uc',['commitment.py','audit','uc_results']),('historical_physics',['independent_review/review.py','--source','.','--out',str(out/'regression')])]:
                step(name,lambda:subprocess.run([sys.executable,'-B',*cmd],cwd=base,check=True))
            assert json.loads((out/'regression/receipt.json').read_bytes())==json.loads((ROOT/'regression/receipt.json').read_bytes())
    rec=dict(status='passed',seconds=time.perf_counter()-begin,wall_seconds_by_check=times,w06_regression=with_regression)
    (out/'C_verification.json').write_text(json.dumps(rec,indent=2)+'\n')
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('out',type=Path);ap.add_argument('--w06',action='store_true');args=ap.parse_args()
    run(args.out.resolve(),args.w06)
