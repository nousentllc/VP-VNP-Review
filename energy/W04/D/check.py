"""Post-run unbounded-clock replay on the canonical unrestricted model, aligned by variable name."""
import argparse,csv,gzip,json,sys,tempfile
from pathlib import Path
from collections import Counter
from uc_warm import HERE,ARMS,np,pe,hs,build,truncate,csc_matrix,csr_matrix
from uc import validate

def check(raw,output):
    rows=[]; counts=Counter(); issues=[]
    for path in sorted((HERE/'inputs').glob('*.json')):
        for T in [12,48]:
            data=truncate(json.loads(path.read_text()),T)
            with tempfile.TemporaryDirectory() as folder:
                tmp=Path(folder)/'instance.json';tmp.write_text(json.dumps(data))
                model,adapter,_=build(data,tmp,'reference')
            h=adapter._solver_model;lp=h.getLp();M=lp.a_matrix_
            matrix=(csc_matrix if M.format_==hs.MatrixFormat.kColwise else csr_matrix)((M.value_,M.index_,M.start_),shape=(lp.num_row_,lp.num_col_))
            vs=list(model.component_data_objects(pe.Var));inds=adapter._pyomo_var_to_solver_var_map
            names=np.empty(lp.num_col_,dtype=object)
            for v in vs:names[inds[id(v)]]=v.name
            integers=np.array([int(x)!=0 for x in lp.integrality_])
            for arm in ARMS:
                folder=raw/f'{path.stem}_{T}_{arm}'
                rec=json.loads((folder/'record.json').read_text()) if (folder/'record.json').is_file() else {'events':[],'stages':[]}
                sup=json.loads((folder/'supervisor.json').read_text()); events=rec['events']
                returned=[e for e in events if 'U' in e and e['t']<=45]
                lower=[e for e in events if 'L' in e and e['t']<=45]
                if returned:
                    with gzip.open(folder/'columns.json.gz','rt') as f: mapping={name:i for i,name in enumerate(json.load(f))}
                    perm=np.array([mapping[name] for name in names])
                    for e in returned:
                        with np.load(folder/e['file']) as z:x=z['x'][perm]
                        ax=matrix@x
                        err=max(0,np.max(lp.row_lower_-ax),np.max(ax-lp.row_upper_),np.max(lp.col_lower_-x),np.max(x-lp.col_upper_),np.max(abs(x[integers]-np.rint(x[integers]))))
                        if err>1e-4 or abs(lp.col_cost_@x+lp.offset_-e['U'])>1e-4:issues.append([folder.name,e['file'],'canonical'])
                        counts['schedules']+=1
                    for v in vs:v.set_value(float(x[inds[id(v)]]),skip_validation=True)
                    if not validate(data,model)['valid']:issues.append([folder.name,'chronology'])
                    g=next(iter(data['thermal_generators']));base=pe.value(model.pg[g,1]);model.pg[g,1].set_value(base+1,skip_validation=True)
                    if validate(data,model)['valid']:issues.append([folder.name,'mutation'])
                    counts['final_schedules']+=1
                row=dict(case=path.stem,hours=T,arm=arm,incumbents=len(returned),first_U_time=min((e['t'] for e in returned),default=None),
                         external_guard=sup['killed'],worker_exit=sup['exit'],build_s=rec.get('build_s'),
                         solver_status=' / '.join(s.get('status','interrupted') for s in rec['stages']))
                for deadline in [5,15,30,45]:
                    u=min((e['U'] for e in returned if e['t']<=deadline),default=None)
                    l=max((e['L'] for e in lower if e['t']<=deadline),default=None)
                    if u is not None and l is not None and l>u+1e-4:issues.append([folder.name,'inverted bound'])
                    row['U'+str(deadline)]=u;row['L'+str(deadline)]=l
                u,l=row['U45'],row['L45'];row['target']=bool(u is not None and l is not None and u-l<=.005*max(1,abs(u))+1e-6)
                transfer=next((s for s in rec['stages'] if s['stage']=='recovered_full'),{})
                row['MIP_start_cost']=transfer.get('transfer_cost')
                logfile=folder/'recovered_full.log'
                logs=logfile.read_text(errors='replace') if logfile.exists() else ''
                row['solver_confirmed_start']=bool('mip start solution is feasible' in logs.lower())
                if row['solver_confirmed_start'] and row['MIP_start_cost'] is None:issues.append([folder.name,'missing start'])
                rows.append(row)
    output.mkdir(parents=True,exist_ok=True)
    with (output/'snapshots.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    (output/'verification.json').write_text(json.dumps(dict(counts=counts,issues=issues),indent=2))
    if issues:raise ValueError(issues)
if __name__=='__main__':check(Path(sys.argv[1]),Path(sys.argv[2]))
