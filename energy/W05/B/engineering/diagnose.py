import argparse,gzip,json,time
from pathlib import Path
import campaign
from diagnostic_model import fleet

def run(source,output):
    rows=list(map(json.loads,gzip.open(source,'rt')))
    with gzip.open(output,'xt') as f:
        for rec in rows:
            if 'failed' not in rec:continue
            z=fleet(rec['seed'],rec['regime'])
            A,b,E,d,c,u,x=[z[k] for k in ['A','b','E','d','c','cap','x0']]
            bad=[(n,v) for n,v in zip(z['labels'],A@x-b) if v>0]
            t=time.perf_counter();lp=campaign.l1_repair(c,A,b,E,d,u,x)
            seconds=time.perf_counter()-t
            q=dict(seed=rec['seed'],regime=rec['regime'],violations=bad,original_model=z.copy(),
                   replacement_lp=lp,anchor_acquisition_s=seconds)
            if lp['code']==0:
                new=lp['x'][:len(x)]
                assert all(A@new<=b) and all(E@new==d) and all(new>=0) and all(new<=u)
                z['x0']=new
                original_provider=campaign.fleet
                try:
                    campaign.fleet=lambda *_:z
                    q['retry']=campaign.one(rec['seed'],rec['regime'])
                except Exception as e:q['retry_error']=repr(e)
                finally:campaign.fleet=original_provider
            f.write(json.dumps(campaign.encode(q),separators=(',',':'))+'\n')
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('primary',type=Path);a.add_argument('new_output',type=Path)
    args=a.parse_args();run(args.primary,args.new_output)
