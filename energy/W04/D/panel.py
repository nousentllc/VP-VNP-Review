"""Two serial lanes, with fixed case assignment and rotated arm order."""
import concurrent.futures,sys,json
from pathlib import Path
from uc_warm import HERE,ARMS,launch
def lane(jobs,out,config):
    for j,path,k,hours in jobs:
        offset=(j+k)%4
        for arm in ARMS[offset:]+ARMS[:offset]:
            dest=launch(path,hours,arm,out,config['candidate_share'],config['effort'])
            print(dest.name,flush=True)
if __name__=='__main__':
    config=json.loads((HERE/'freeze.json').read_text());out=Path(sys.argv[1])
    jobs=[(j,p,k,h) for j,p in enumerate(sorted((HERE/'inputs').glob('*.json'))) for k,h in enumerate([12,48])]
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
        futures=[ex.submit(lane,jobs[n::2],out,config) for n in range(2)]
        for f in futures:f.result()
