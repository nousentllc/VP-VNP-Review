"""Read-only cross-check of delivered inputs, mathematical witnesses, and recorded schedules."""
import argparse
import csv
import gzip
import hashlib
import json
import re
import tempfile
from collections import Counter
from decimal import Decimal
from pathlib import Path
import numpy as np
import pyomo.environ as pe
from common import ROOT,OUT,DESIGN
from battery_model import arrays,model
from battery_audit import exact_box,direct
from ac import read_case,independent
from uc import truncate,build,validate


def need(condition,detail):
    if not condition:raise ValueError(detail)


def verify():
    freeze=json.loads((ROOT/'protocol/freeze.json').read_text())
    forecast=json.loads((ROOT/'protocol/forecast_freeze.json').read_text())
    frozen={**freeze['sha256'],**freeze['public_input_sha256'],**forecast['sha256']}
    for name,expected in frozen.items():
        need(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==expected,name)
    cases={r['id']:arrays(r) for r in json.loads((ROOT/'inputs/battery_holdout.json').read_text())}
    trials=[json.loads(l) for l in gzip.open(OUT/'A/holdout.jsonl.gz','rt')]
    expected={(k,m,i) for k,a in cases.items() for m in DESIGN['A']['policies']
              if m!='symmetry' or a['cohort']=='interchangeable' for i in range(DESIGN['A']['repeats'])}
    need(len(trials)==len(expected) and {(x['case'],x['policy'],x['repeat']) for x in trials}==expected,'A denominators')
    total=0
    for x in trials:
        a=cases[x['case']]
        if x['target_time'] is not None:
            need(x['target_time']<=2 and x['upper']-x['lower'] <= 2e-5+.001*max(1,abs(x['upper'])),'A target')
        if x['repeat']!=0:continue
        obj,err=direct(a,x['best_powers'])
        need(err<=2e-6 and abs(x['upper']-obj)<1e-5,'A incumbent')
        total+=1
        for step in x['steps']:
            if 'returned_powers' in step:
                obj,err=direct(a,step['returned_powers'])
                need((err<=2e-6)==step['returned_check']['valid'] and abs(obj-step['returned_check']['cost'])<1e-5,'A raw return')
                total+=1
    certs=json.loads((OUT/'A/exact_lp_certificates.json').read_text())
    need(len(certs)==len(cases),'LP certificates')
    for cert in certs:
        a=cases[cert['case']]
        m,_,_=model(a,[[i] for i in range(a['n'])],'lp')
        need(str(exact_box(m,cert['row_dual']))==cert['exact_lower'],'exact lower')
    b=json.loads((OUT/'B/checks.json').read_text());blog=(OUT/'B/lean-build.log').read_text()
    need('sorryAx' not in blog and 'error:' not in blog and len(b['proofs'])==16,'Lean log')
    need(all(x['exit']!=0 for x in b['negative_compile_controls']),'negative Lean controls')
    need(b['source_sha256']==hashlib.sha256((ROOT/'formal/Storage.lean').read_bytes()).hexdigest(),'Lean source')
    refs={}
    for line in (ROOT/'inputs/ac/BASELINE.md').read_text().splitlines():
        if line.startswith('| pglib_'):
            fields=[x.strip() for x in line.split('|')];refs[fields[1]]=Decimal(fields[5])
    c=json.loads((OUT/'C/runs.json').read_text())
    need(len(c)==36 and len({(x['case'],x['policy'],x['repeat']) for x in c})==36,'C denominator')
    c_mut=0
    for x in c:
        case=read_case(ROOT/'inputs/ac'/(x['case']+'.m'))
        values=[np.array(z) for z in x['variables']];check=independent(case,*values)
        need(check['valid']==x['check']['valid'] and abs(check['cost']-x['check']['cost'])<1e-6,'C raw vector')
        target=refs[x['case']]
        need(Decimal(str(check['cost'])).quantize(Decimal(1).scaleb(target.as_tuple().exponent))==target,'PGLib published AC objective')
        values[2][0]+=1.
        need(not independent(case,*values)['valid'],'C faulty generation vector');c_mut+=1
    dcount=0;dmut=0;miss=0;drows=sorted((OUT/'D').glob('*.json'))
    need(len(drows)==8,'D denominator')
    for f in drows:
        r=json.loads(f.read_text())
        if not r.get('schedule_file'):
            need(not r['validated_by_deadline'],'D missing schedule');miss+=1;continue
        data=truncate(json.loads((ROOT/'inputs/uc'/(r['instance']+'.json')).read_text()),r['hours'])
        with tempfile.TemporaryDirectory() as tmp:
            inst=Path(tmp)/'instance.json';inst.write_text(json.dumps(data))
            m,adapter,pairs=build(data,inst,r['policy'])
        with np.load(OUT/'D'/r['schedule_file'],allow_pickle=False) as archive:
            vars=list(m.component_data_objects(pe.Var,active=True))
            names=archive['names'].tolist()
            lookup=dict(zip(names,archive['values']))
            need(len(lookup)==len(names)==len(vars) and set(lookup)=={v.name for v in vars},
                 'UC variable identity in '+r['id'])
            for v in vars:v.set_value(float(lookup[v.name]),skip_validation=True)
        replay=validate(data,m)
        need(replay['valid']==r['check']['valid'] and abs(replay['objective']-r['check']['objective'])<1e-5,'UC reread')
        if dmut==0:
            gen=next(iter(data['thermal_generators']));m.pg[gen,1].set_value(m.pg[gen,1].value+1)
            need(not validate(data,m)['valid'],'UC faulty dispatch');dmut+=1
        dcount+=1
    inp=json.loads((ROOT/'inputs/load_forecasts.json').read_text())
    site=inp['parameters']
    lookup={x['id']:x for x in inp['cases']}; erows=json.loads((OUT/'E/runs.json').read_text())
    need(len(erows)==72 and len({(x['case'],x['method']) for x in erows})==72,'E denominator')
    checked=0
    for r in erows:
        a=lookup[r['case']];prev=site['previous'];e=site['initial'];loss=useful=0.
        for i,(g,ch,dis,u,end) in enumerate(r['actions']):
            avail=a['available'][i];p=site['power']*avail
            issue=a['issues'][i]
            need(issue['issue']==i and issue['valid'][0]==i and issue['load'][0]==a['load'][i],'forecast issue')
            tol=1e-6; e+=ch*site['eta_c']-dis/site['eta_d']
            need(abs(e-end)<tol and a['floor'][i]-tol<=e<=site['energy']+tol,'E SOC')
            need(-tol<=g<=site['grid_cap']+tol and abs(g-prev)<=site['ramp']+tol,'E grid')
            need(-tol<=ch<=p+tol and -tol<=dis<=max(0,p-a['reserve'][i])+tol and min(ch,dis)<=tol,'E device')
            need(abs(g+dis-ch+u-a['load'][i])<=tol and -tol<=u<=a['load'][i]-site['facility']+tol,'E load')
            useful+=a['load'][i]-site['facility']-u
            loss+=ch*(1-site['eta_c'])+dis*(1/site['eta_d']-1)
            prev=g;checked+=1
        need(abs(useful-r['useful_compute_MWh'])<1e-6 and abs(loss-r['conversion_loss_MWh'])<1e-6 and e>=95-tol,'E totals')
    legacy=json.loads((OUT/'E/legacy_replay.json').read_text())
    reference=json.loads((ROOT/'inputs/legacy/historical_bess_metrics.json').read_text())
    for new in legacy:
        old=next(r for r in reference if (r['profile'],r['method'])==(new['profile'],new['method']))
        for k in ['unserved_MWh','grid_MWh','throughput_MWh','conversion_loss_MWh','terminal_MWh']:
            need(abs(old[k]-new[k])<1e-6,'historical W-E05 '+k)
    return dict(frozen_hashes=len(frozen),A_trials=len(trials),A_schedules=total,exact_lp_bounds=len(certs),
                Lean_axiom_records=len(b['proofs']),C_checks=len(c),C_corruptions_rejected=c_mut,
                D_schedules=dcount,D_missing=miss,D_corruptions_rejected=dmut,
                E_device_hours=checked,legacy_profiles_and_policies_verified=len(legacy))


if __name__=='__main__': print(json.dumps(verify(),indent=2))
