"""Rebuild the canonical W03 source and W04 modules, then test deliberate false claims."""
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

HERE = Path(__file__).resolve().parent
W03 = HERE.parent / 'foundation' / 'formal'
MODULES = ('Storage', 'AIPC', 'StorageContract', 'Controls', 'Sharpness', 'Inventory')
WHITELIST = {'propext', 'Classical.choice', 'Quot.sound'}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def packages_from_lock(root):
    if digest(W03/'Storage.lean') != 'd719dae3bd49c0aedef8d0290c663e73e77862512bee4252afc4bc57f69c5413':
        raise ValueError('W03 source differs from the campaign input')
    if digest(W03/'lake-manifest.json') != '1dc07eb8e535918953da117ff0c6f79145a3ac958889f483f73fc184743a3a99':
        raise ValueError('W03 dependency lock differs from the campaign input')
    lock = json.loads((W03/'lake-manifest.json').read_text())['packages']
    rows = []
    for spec in lock:
        directory = root/spec['name']
        actual = subprocess.check_output(['git','-C',str(directory),'rev-parse','HEAD'],text=True).strip()
        if actual != spec['rev']:
            raise ValueError((spec['name'], spec['rev'], actual))
        rows.append({'name':spec['name'], 'revision':actual})
    return rows


def run(args):
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    packages = args.packages.resolve()
    lean = str(args.lean.resolve())
    version = subprocess.check_output([lean,'--version'],text=True).strip()
    if '4.30.0-rc2' not in version:
        raise ValueError(version)
    lock = packages_from_lock(packages)
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    if not args.skip_w03:
        subprocess.run([sys.executable,str(W03/'verify.py'),'--packages',str(packages),
                        '--lean',lean,'--out',str(out/'w03')],env=env, check=True)
    with tempfile.TemporaryDirectory() as tmp:
        build = Path(tmp)
        libraries = [packages/r['name']/'.lake/build/lib/lean' for r in lock]
        env['LEAN_PATH'] = os.pathsep.join(map(str,[build,*libraries]))
        record = {'toolchain':version,'packages':lock,'modules':{},'axioms':{}}
        def compile_source(module, emit=True):
            src = (W03 if module == 'Storage' else HERE/'formal')/(module+'.lean')
            shutil.copyfile(src, build/src.name)
            cmd = [lean,'-j1']
            if emit:
                cmd += ['-o',module+'.olean']
            p = subprocess.run(cmd+[src.name],cwd=build,env=env,text=True,
                               stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
            (out/(module+'.log')).write_text(p.stdout)
            if emit and p.returncode:
                raise RuntimeError(f'{src.name} exited {p.returncode}. See {out/(module+".log")}')
            return p,src
        for module in MODULES:
            proc,src = compile_source(module)
            record['modules'][module] = {'source_sha256':digest(src),'exit':proc.returncode}
        inspect = (out/'Inventory.log').read_text()
        for name, names in re.findall(r"'([^']+)' depends on axioms: \[([^\]]*)\]", inspect):
            axioms = [x.strip() for x in names.split(',') if x.strip()]
            if not set(axioms) <= WHITELIST:
                raise ValueError((name,axioms))
            record['axioms'][name] = axioms
        for name in re.findall(r"'([^']+)' does not depend on any axioms", inspect):
            record['axioms'][name]=[]
        requested = re.findall(r'^#print axioms (\S+)$',(HERE/'formal/Inventory.lean').read_text(),re.M)
        if set(requested) != set(record['axioms']):
            raise ValueError(('Missing declaration or unrecognized inspection',set(requested)-set(record['axioms'])))
        rejected,source = compile_source('Mutants',emit=False)
        rejected_lines = list(map(int,re.findall(r'Mutants.lean:(\d+):\d+: error:',rejected.stdout)))
        expected = [i for i,line in enumerate(source.read_text().splitlines(),1) if line.startswith('example')]
        if rejected.returncode == 0 or rejected_lines != expected:
            raise ValueError((rejected.returncode,rejected_lines,expected))
        record['mutants']={'source_sha256':digest(source),'exit':rejected.returncode,'rejected_lines':rejected_lines}
    exact = subprocess.check_output([sys.executable,str(HERE/'exact_controls.py')],text=True,env=env)
    (out/'exact_controls.json').write_text(exact)
    (out/'verification.json').write_text(json.dumps(record,indent=2,sort_keys=True)+'\n')


if __name__ == '__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--packages',type=Path,required=True)
    ap.add_argument('--lean',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--skip-w03',action='store_true',help='Skip historical W03 control runner only.')
    run(ap.parse_args())
