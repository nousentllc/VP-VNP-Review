"""Reproduce a single arm, the pre-freeze development panel or the sealed campaign."""
from pathlib import Path
from fractions import Fraction as F
from time import perf_counter as clock
import csv, gzip, hashlib, json, platform, resource, subprocess, sys
from datetime import datetime, timezone
from itertools import product
from tempfile import TemporaryDirectory

import independent as I
import model as M

BASE=Path(__file__).resolve().parent
DESIGN=json.loads((BASE/'design.json').read_text())
STAGES=DESIGN['stages']
ARMS=['staged','direct','milp']

def dump(path,data):
    path.write_text(json.dumps(data,ensure_ascii=False,sort_keys=True,indent=2,default=str)+'\n')

def measure(f,*args):
    start=clock(); val=f(*args)
    return val,clock()-start

def bounds(table,name):
    if name=='analytic':
        return M.meter_floor(table), None
    if name=='causal':
        return M.rolling(table,6)
    value=M.relaxation(table,{'PF':0,'prefix1':1,'prefix3':3,'penalty':0}[name],name=='penalty')
    return value, None

def disclosure(table):
    """Issue-time forecasts and original leaf weights; exported for independent inspection."""
    issued={}
    for t in range(6):
        for bits in product('01',repeat=t):
            h=''.join(bits)
            observed, forecast=M.public(table,h)
            issued[h]={'realized':observed,'next_q_price_cap':list(map(str,forecast)) if forecast else None}
    return dict(issued=issued,leaf_weights={s:str(w) for s,w in M.leaves(table,0,0)})

def leak_test(table,policy):
    records=[]; seen=set()
    for leaf in I.BITS:
        s,r=2,0
        for t in range(6):
            history=leaf[:t]
            a=policy[history]
            records.append((history,s,r,a)); seen.add(history)
            if t<5:
                modified=leaf[:t]+''.join('0' if ch=='1' else '1' for ch in leaf[t:])
                assert modified!=leaf and modified[:t]==history
                assert M.public(table,modified[:t])==M.public(table,history)
            s+=a;r=a
    I.reject_leak(records); I.reject_leak(reversed(records))
    return {'prefix_state_actions':len(records),'realized_public_nodes':len(seen),
            'suffix_flips_tested':len(I.BITS)*5,'future_conflict_mutation':I.controls()['leaked_action_rejected']}

def worker(kind,seed,arm):
    start=clock(); table,setup=measure(M.law,kind,seed)
    (candidate,internal),build=measure(M.portfolio,table)
    tcheck=clock()
    verified={key:I.audit(table,'policy',tape) for key,tape in candidate.items()}
    assert all(verified[key]==value for key,value in internal.items())
    selected=min(verified,key=verified.get)
    baseline,actions=verified[selected],candidate[selected]
    check=clock()-tcheck
    threshold=max(F(15),abs(F(baseline))/100); stages=[]; exact_witness=None; native=None
    times=dict(law=setup,baseline_build=build,baseline_check=check)
    strongest=None
    if arm=='milp':
        from native import solve
        native,elapsed=measure(solve,table)
        primal,verify=measure(I.audit,table,'policy',native['policy'])
        assert abs(float(primal)-native['objective'])<1e-6 and native['integer_residual']<1e-6
        stages.append(dict(tier='milp',value=str(primal),solve=elapsed,check=verify,
                           interpretation='exact feasible policy only; dual numerical'))
    else:
        for name in (['causal'] if arm=='direct' else STAGES):
            (value,witness),solve_t=measure(bounds,table,name)
            start_check=clock(); compare=I.audit(table,name)
            assert value==compare,(name,value,compare)
            centered=None
            if name=='penalty':
                centered=I.audit(table,'center_count')
            if witness is not None:
                assert I.audit(table,'policy',witness)==value
                exact_witness=witness
            verify=clock()-start_check
            strongest=value if strongest is None else max(strongest,value)
            stages.append(dict(tier=name,value=str(value),checked_best=str(strongest),solve=solve_t,
                               check=verify,uniform_centers=centered))
            if arm=='staged' and baseline-strongest<threshold:
                break
    result=dict(stratum=kind,seed=seed,arm=arm,baseline=str(baseline),threshold=str(threshold),
                times=times,stages=stages,portfolio_values={k:str(v) for k,v in verified.items()},selected=selected,baseline_policy=actions,exact_policy=exact_witness,native=native)
    if arm=='shadow':
        if kind=='positive':
            tape={h:(1,1,0,0,-1,-1)[len(h)] for h in actions}
            plant=I.audit(table,'policy',tape)
            result['planted_witness_value']=str(plant)
            result['planted_witness_gain']=str(baseline-plant)
        result.update(tables=table,information=disclosure(table),leak=leak_test(table,actions))
    result['worker_seconds']=clock()-start
    result['rss_native']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return result

def locked():
    lock=json.loads((BASE/'freeze.json').read_text())
    for f,sha in lock['files'].items():
        assert hashlib.sha256((BASE/f).read_bytes()).hexdigest()==sha, f

def campaign(out,dev=False):
    out.mkdir(parents=True,exist_ok=True)
    if not dev:
        locked()
    families=(list(zip(DESIGN['holdout_by_stratum'],DESIGN['development_seeds'])) if dev else
              [(k,seed) for k,seeds in DESIGN['holdout_by_stratum'].items() for seed in seeds])
    start=clock(); summary=[]; raw=[]
    for ix,(kind,seed) in enumerate(families):
        # Rotation counters deterministic arm-order effects. Shadow is separate from timed arms.
        arms=ARMS[ix%3:]+ARMS[:ix%3]+['shadow']
        record={}
        for arm in arms:
            begin=clock()
            p=subprocess.run([sys.executable,str(BASE/'run.py'),'worker',kind,str(seed),arm],
                             text=True,capture_output=True)
            elapsed=clock()-begin
            if p.returncode:
                dump(out/f'failure_{kind}_{seed}_{arm}.json',dict(exit=p.returncode,stdout=p.stdout,stderr=p.stderr))
                raise RuntimeError(p.stderr)
            row=json.loads(p.stdout);row['process_seconds']=elapsed
            row['worker_stderr']=p.stderr
            record[arm]=row;raw.append(row)
        sh=record['shadow']; u=F(sh['baseline']); gate=F(sh['threshold'])
        v={b['tier']:F(b['value']) for b in sh['stages']}
        native=record['milp']['native']
        assert v['analytic']<=v['PF']<=v['prefix1']<=v['prefix3']<=v['causal']<=u
        assert v['penalty']<=v['causal']
        assert abs(float(v['causal'])-native['dual_float'])<1e-6
        assert F(record['milp']['stages'][0]['value'])==v['causal']
        stopping=record['staged']['stages'][-1]
        ruled=u-F(stopping['checked_best'])<gate
        assert not (ruled and u-v['causal']>=gate)
        summary.append(dict(stratum=kind,seed=seed,weight=str(F(1,len(families))),baseline=str(u),
            threshold=str(gate),**{k:str(x) for k,x in v.items()},gain=str(u-v['causal']),
            first_stop=stopping['tier'] if ruled else 'demonstrated',decision='excluded' if ruled else 'demonstrated',
            direct_s=record['direct']['process_seconds'],staged_s=record['staged']['process_seconds'],
            milp_s=record['milp']['process_seconds']))
        proof={}
        for mode in ('causal','center_count'):
            cert={}
            result=I.audit(sh['tables'],mode,proof=cert)
            proof[mode]={'value':str(result),'entries':cert}
        with (out/f'proof_{seed}.json.gz').open('wb') as stream:
            stream.write(gzip.compress(json.dumps(proof,sort_keys=True).encode(),mtime=0))
        print(kind,seed,summary[-1]['first_stop'],flush=True)
    dump(out/'records.json',raw);dump(out/'controls.json',I.controls())
    with (out/'families.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(summary[0]));w.writeheader();w.writerows(summary)
    dump(out/'run.json',dict(families=len(families),elapsed_before_receipt=clock()-start,
         host=platform.platform(),python=sys.version,rss_units='bytes on Darwin; KiB on Linux',
         executable=sys.executable,completed_utc=datetime.now(timezone.utc).isoformat()))
if __name__=='__main__':
    if sys.argv[1]=='worker':
        print(json.dumps(worker(sys.argv[2],int(sys.argv[3]),sys.argv[4]),default=str))
    else:
        campaign(Path(sys.argv[2]),sys.argv[1]=='dev')
