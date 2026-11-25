"""Fingerprint the compiler, critical imported objects and all dependency checkouts."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inspect(lean, packages, foundation):
    declarations = json.loads((foundation/'lake-manifest.json').read_text())['packages']
    deps = []
    for row in declarations:
        root = packages/row['name']
        commit = subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()
        if commit != row['rev']:
            raise ValueError(('commit differs from lock',row['name'],commit))
        # Compare tracked files only; the intentionally untracked build cache is separately sampled.
        check = subprocess.run(['git','--no-optional-locks','-C',str(root),'diff','--quiet','HEAD','--'])
        if check.returncode not in (0,1):
            raise RuntimeError(f'Git diff failed for {root}')
        deps.append({'name':row['name'],'commit':commit,'tracked_source_differences':bool(check.returncode)})
    imports=['Mathlib','Mathlib/Data/Real/Archimedean','Mathlib/Order/ConditionallyCompleteLattice/Basic',
             'Mathlib/Tactic/Linarith','Mathlib/Tactic/NormNum']
    base=packages/'mathlib'/'.lake/build/lib/lean'
    return {'lean_version':subprocess.check_output([str(lean),'--version'],text=True).strip(),
            'executable_sha256':sha(lean),'lockfile_sha256':sha(foundation/'lake-manifest.json'),
            'checked_package_sources':deps,'sampled_import_objects_sha256':{i:sha(base/(i+'.olean')) for i in imports},
            'scope':'Prebuilt dependency cache; neither all dependency objects nor compiler rebuilt from source.'}


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--lean',type=Path,required=True)
    ap.add_argument('--packages',type=Path,required=True)
    a=ap.parse_args()
    print(json.dumps(inspect(a.lean,a.packages,Path(__file__).resolve().parent.parent/'foundation/formal'),
                     sort_keys=True,indent=2))
