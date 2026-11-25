"""Negative controls for the schedule-to-original-model interface."""
import argparse
import json
from pathlib import Path
import numpy as np
from campaign import HERE, arrays, complete_start, model, validate
from battery_audit import direct


def audit(path):
    results=[]
    for item in json.loads((HERE/'protocol/instances.json').read_text()):
        a=arrays(item);c=a['fallback_charge'];d=a['fallback_discharge']
        if not validate(a,c,d)['valid']:raise ValueError(a['id'])
        faulty=c.copy()
        faulty[0,0]=a['power'][0]+1
        check=validate(a,faulty,d)
        _,err=direct(a,(faulty,d))
        if check['valid'] or err<=2e-6:raise ValueError('Bad power control accepted')
        groups=[[i] for i in range(a['n'])]
        m,_,_=model(a,groups);h=m.solver('on',1e-6)
        v=complete_start(a,c,d,groups)
        def worst(vec):
            y=m.A@vec
            return max(0,np.max(np.asarray(m.lo)-vec),np.max(vec-np.asarray(m.hi)),np.max(np.asarray(m.lhs)-y),np.max(y-np.asarray(m.rhs)))
        base=worst(v)
        # Same powers but inject a bad value into the transferred terminal state.
        v[2*a['n']*a['t']+a['t']-1]+=1
        mutated=worst(v)
        if base>2e-6 or mutated<.99:raise ValueError('Solver matrix controls disagree')
        results.append(dict(case=a['id'],fallback_residual=float(base),corrupt_charge_violation=float(err),
                            corrupted_start_state_violation=float(mutated)))
    path.write_text(json.dumps(results,separators=(',',':'))+'\n')


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True)
    audit(ap.parse_args().out)
