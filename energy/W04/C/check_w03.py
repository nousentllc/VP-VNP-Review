"""Compare fresh W03 AC replay against the exact original stored trajectories."""
import json
import sys
from pathlib import Path

def run(fresh, original, output):
    def index(path):
        return {(x['case'],x['policy'],x['repeat']):x for x in json.loads(path.read_text())}
    a,b=index(fresh),index(original)
    assert set(a)==set(b) and len(a)==36
    pairs=[(x,b[key]) for key,x in a.items() if x.get('check',{}).get('valid') and b[key].get('check',{}).get('valid')]
    record=dict(trials=len(a),fresh_valid=sum(bool(x.get('check',{}).get('valid')) for x in a.values()),
                fresh_valid_by_deadline=sum(bool(x.get('check',{}).get('valid')) and x['within_deadline'] for x in a.values()),
                paired_valid=len(pairs),max_abs_cost_delta=max(abs(x['check']['cost']-y['check']['cost']) for x,y in pairs))
    output.write_text(json.dumps(record,indent=2)+'\n')

if __name__=='__main__':run(*(Path(x) for x in sys.argv[1:]))
