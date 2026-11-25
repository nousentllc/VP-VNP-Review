"""Secondary native linear-solver diagnostic with separate wall accounting."""
import json,sys
from pathlib import Path
from opf import HERE,W04,CFG,solve,save
if __name__=='__main__':
    path,arm,out=Path(sys.argv[1]),sys.argv[2],Path(sys.argv[3]);out.mkdir(exist_ok=True,parents=True)
    cfg=json.loads((W04/'foundation/results/C/development.json').read_text());opts=dict(cfg['trials'][0]['options'])
    opts.update({'ipopt.mu_strategy':cfg['mu_strategy'],'ipopt.mumps_print_level':3,'ipopt.print_level':7})
    CFG['seconds_per_policy']=60
    r=solve(path,arm,1,opts,out);r['supplemental_valid_60s']=r['check']['valid'] and r['elapsed']<=60
    save(out/(path.stem+'_'+arm+'.json'),r)
