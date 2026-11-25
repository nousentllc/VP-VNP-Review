"""One instrumented repetition per case and arm, separate from registered timing."""
import argparse, gzip, json, shutil, subprocess, sys, time
from pathlib import Path
HERE=Path(__file__).resolve().parent
def run(out):
    out.mkdir(parents=True,exist_ok=False)
    arms=['full_dc','full_matched','all','degree','guided']
    def size(p):return int(p.stem.split('case')[1].split('_')[0])
    for i,path in enumerate(sorted((HERE/'inputs').glob('*.m'),key=size)):
        for arm in arms[i:]+arms[:i]:
            name=path.stem+'_'+arm
            console=out/(name+'.native')
            stamp=time.monotonic()
            try:
                with console.open('w') as f:
                    p=subprocess.run([sys.executable,str(HERE/'profile.py'),str(path),arm,str(out)],
                             stdout=f,stderr=subprocess.STDOUT,timeout=110)
                result=dict(exit=p.returncode,watchdog=False)
            except subprocess.TimeoutExpired:result=dict(exit=None,watchdog=True)
            result['process_wall_s']=time.monotonic()-stamp
            (out/(name+'.run.json')).write_text(json.dumps(result))
            with console.open('rb') as src,gzip.open(console.with_suffix('.native.gz'),'wb') as dest:shutil.copyfileobj(src,dest)
            console.unlink()
        print(path.stem,flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('out',type=Path);run(p.parse_args().out)
