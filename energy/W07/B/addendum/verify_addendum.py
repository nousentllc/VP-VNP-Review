"""Secondary verification of the explicit real-infimum qualification."""
import argparse, hashlib, json, os, re, shutil, subprocess, sys, tempfile, time
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.dont_write_bytecode=True
sys.path.insert(0,str(HERE.parent))
from verify import ALLOWED, EXPECTED_COMPILER, read_pins, sha


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--lean',type=Path,required=True)
    parser.add_argument('--packages',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    out=args.out.resolve()
    out.mkdir(parents=True,exist_ok=True)
    if list(out.iterdir()):
        raise ValueError('Use a fresh results directory')
    start=time.perf_counter()
    lean=args.lean.resolve()
    release=subprocess.check_output([lean,'--version'],text=True).strip()
    assert EXPECTED_COMPILER in release
    packages=args.packages.resolve()
    pins=read_pins(packages)
    for rel,h in json.loads((HERE/'lock.json').read_text())['sha256'].items():
        assert sha(HERE/rel)==h,rel
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp)
        env=dict(os.environ,LEAN_PATH=os.pathsep.join(map(str,[root,*[
            packages/item['name']/'.lake/build/lib/lean' for item in pins]])))
        for name,src in [('Information',HERE.parent/'formal/Information.lean'),('Infimum',HERE/'Infimum.lean')]:
            shutil.copy2(src,root/src.name)
            proc=subprocess.run([lean,'-j1','-o',name+'.olean',src.name],cwd=root,env=env,
                                text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
            (out/(name+'.log')).write_text(proc.stdout)
            assert proc.returncode==0 and 'warning:' not in proc.stdout, proc.stdout
        matches=re.findall(r"'(W07.Extra.\w+)' depends on axioms: \[([^\]]+)\]",proc.stdout)
        axioms={k:v.split(', ') for k,v in matches}
        assert len(axioms)==4 and all(set(a)<=ALLOWED for a in axioms.values())
        assert proc.stdout.count('LOCAL-EDGES')==4
        replay=subprocess.run([lean.with_name('leanchecker'),'-v','Infimum'],cwd=root,env=env,
                              text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        (out/'kernel_Infimum.log').write_text(replay.stdout)
        assert replay.returncode==0 and 'replaying Infimum' in replay.stdout
    (out/'audit.json').write_text(json.dumps(dict(lean=release,source_pins=len(pins),
        axioms=axioms,local_edges=4,replay_exit=replay.returncode,seconds=time.perf_counter()-start),
        sort_keys=True,indent=2)+'\n')


if __name__=='__main__':
    main()
