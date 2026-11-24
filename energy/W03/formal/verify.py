"""Compile storage statements, inspect axiom output and run independent counterexamples."""
import argparse
import hashlib
import json
import os
import subprocess
import tempfile
from fractions import Fraction as F
from pathlib import Path

HERE=Path(__file__).resolve().parent


def finite_checks():
    transitions=0
    for n in range(1,8):
        for cap in range(1,7):
            lift=lambda s:[(s+i)//n for i in range(n)]
            for s in range(n*cap+1):
                x=lift(s)
                assert sum(x)==s and max(x)<=cap
                for rate in range(4):
                    for u in range(max(0,s-n*rate),min(n*cap,s+n*rate)+1):
                        delta=[b-a for a,b in zip(x,lift(u))]
                        assert max(map(abs,delta))<=rate and sum(map(abs,delta))==abs(u-s)
                        transitions+=1
    # A small positive terminal interval permits a nonzero cycle in a fixed class.
    c,d=F(1),F(4,5)
    rho=(F(4,5),F(81,100))
    weights=[F(1,2)]*2
    ed=[F(1),F(9,10)]
    eps=[abs(w*(r*c-d)/e) for r,w,e in zip(rho,weights,ed)]
    right=sum(e*z/w for e,z,w in zip(ed,eps,weights))
    assert abs(rho[0]-rho[1])*c==right==F(1,100)
    return dict(integer_transitions=transitions,nonzero_terminal_tolerance_case={
        'C':str(c),'D':str(d),'SOC_tolerances':list(map(str,eps)),'both_sides':str(right)})


def run(packages,lean,out):
    out.mkdir(parents=True,exist_ok=True)
    env=os.environ.copy()
    if packages:
        packages=packages.resolve()
        rev=subprocess.check_output(['git','-C',str(packages/'mathlib'),'rev-parse','HEAD'],text=True).strip()
        if rev!='896cc56a395e1615786fac56564a3fe6bfeebcc4': raise ValueError('Unexpected mathlib revision')
        env['LEAN_PATH']=os.pathsep.join(str(x) for x in sorted(packages.glob('*/.lake/build/lib/lean')))
        command=[lean]
    else:
        command=['lake','env','lean']
    version=subprocess.check_output(command+['--version'],cwd=HERE,env=env,text=True).strip()
    if '4.30.0-rc2' not in version:raise ValueError(version)
    def compile_file(path):
        return subprocess.run(command+[str(path)],cwd=HERE,env=env,capture_output=True,text=True)
    primary=compile_file(HERE/'Storage.lean')
    log=primary.stdout+primary.stderr
    (out/'lean-build.log').write_text(log)
    if primary.returncode or 'sorryAx' in log or 'error:' in log:
        raise ValueError(log)
    controls={
        'mismatched_labels': '((0 : ℤ) = |(1:ℤ)-0| + |(0:ℤ)-1|)',
        'remove_efficiency_difference': '((4/5 : ℚ)*1=4/5 ∧ (4/5 : ℚ)*1=4/5) → (1 : ℚ)=0',
        'permit_fractional_individual_modes': '((4/5 : ℚ)*(1/2)-(8/25)/(4/5)=0 ∧ 2*((1/2:ℚ)-8/25)=9/25) → min (1/2:ℚ) (8/25)=0',
        'terminal_interval_implies_zero_throughput': '(|(4/5:ℚ)*1-4/5|≤0 ∧ |(81/100:ℚ)*1-4/5|≤1/100) → (1:ℚ)≤0',
    }
    negatives=[]
    with tempfile.TemporaryDirectory() as temp:
        for name,goal in controls.items():
            p=Path(temp)/(name+'.lean')
            p.write_text('import Mathlib\nexample : '+goal+' := by norm_num\n')
            res=compile_file(p)
            if res.returncode==0 or 'unsolved goals' not in res.stdout:
                raise ValueError((name,res.stdout,res.stderr))
            negatives.append({'control':name,'proposition':goal,'exit':res.returncode,
                              'diagnostic':res.stdout[res.stdout.index('error:'):].strip()})
    from replay_controls import check_labeled_endpoints, check_schedule_averaging
    rec=dict(toolchain=version,source_sha256=hashlib.sha256((HERE/'Storage.lean').read_bytes()).hexdigest(),
             proofs=[ln.split("'")[1] for ln in log.splitlines() if 'depends on axioms' in ln],
             negative_compile_controls=negatives,exact_checks=finite_checks(),labeled=check_labeled_endpoints(),
             averaged=check_schedule_averaging(),certificate={'positive':1,'corruptions_rejected':4})
    (out/'checks.json').write_text(json.dumps(rec,indent=2)+'\n')


if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--packages',type=Path)
    ap.add_argument('--lean',default='lean')
    ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args()
    run(args.packages,args.lean,args.out.resolve())
