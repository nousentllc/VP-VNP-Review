"""Independent AC replay and a direct small-graph test of the symbolic fill counter."""
import csv,json,sys
from pathlib import Path
from opf import HERE,read_case,independent,np
from structure import symbolic,sp
def direct_symbolic(g,perm):
    a=g.toarray()[np.ix_(perm,perm)].astype(bool);np.fill_diagonal(a,False);count=len(perm)
    for j in range(len(perm)):
        ids=np.flatnonzero(a[j,j+1:])+j+1
        count+=len(ids);a[np.ix_(ids,ids)]=True
    return count
def run(raw,out):
    rng=np.random.default_rng(611)
    for i in range(25):
        x=rng.random((25,25))<.1;g=sp.csc_matrix((x|x.T)|np.eye(25,dtype=bool))
        count,perm=symbolic(g)
        if direct_symbolic(g,perm)!=count:raise ValueError('Symbolic factor count')
    rows=[]
    for p in sorted(raw.glob('*.json')):
        r=json.loads(p.read_text());name=r['case'];dt=r.get('elapsed')
        check=None
        if 'variables' in r:
            a=read_case(HERE/'inputs'/(name+'.m'));v=[np.asarray(z) for z in r['variables']]
            check=independent(a,*v)
            if check['valid']!=r['check']['valid'] or abs(check['cost']-r['check']['cost'])>1e-5:raise ValueError(name)
            v[2][0]+=1
            if independent(a,*v)['valid']:raise ValueError('corruption accepted')
        diag=r.get('structure',{})
        rows.append(dict(case=name,policy=r['policy'],repeat=r['repeat'],status=r.get('status',r.get('error')),elapsed=dt,
                admissible=bool(check and check['valid']),on_time=bool(check and check['valid'] and dt<=12),
                cost=None if check is None else check['cost'],lower=r.get('lower'),iterations=r.get('iterations'),
                build=r.get('build_seconds'),validation=r.get('validation_s'),rss=r.get('rss_bytes'),
                n=r.get('n_variables'),m=r.get('constraint_rows'),jac=r.get('jacobian_nnz'),
                hess=diag.get('hessian_nnz'),fill=diag.get('added_lower_fill'),condition=diag.get('condition_1_est'),
                proxy_factor_s=diag.get('proxy_factor_s')))
    if len(rows)!=160 or len({(r['case'],r['policy'],r['repeat']) for r in rows})!=160:raise ValueError('Missing AC trials')
    out.mkdir(parents=True,exist_ok=True)
    with (out/'comparison.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    (out/'verification.json').write_text(json.dumps(dict(trials=len(rows),valid_by_deadline=sum(r['on_time'] for r in rows),
        raw_vectors=sum(r['cost'] is not None for r in rows),direct_symbolic_controls=25)))
if __name__=='__main__':run(Path(sys.argv[1]),Path(sys.argv[2]))
