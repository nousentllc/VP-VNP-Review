"""Supplemental reconstruction of the five baseline candidates from each public scenario law.

This audit was written after results were available. The comparator, inputs, costs,
portfolio values and selected policy are original locked-code outputs.
"""
from functools import lru_cache
from fractions import Fraction as F
from itertools import product
from pathlib import Path
import json

import independent as I

def replay(table, slope):
    action_order=(0,-1,1)
    @lru_cache(None)
    def terminal_safe(remaining, stock, last):
        for plan in product((-1,0,1),repeat=remaining):
            s,r=stock,last
            for a in plan:
                if not (abs(a-r)<=1 and 0<=s+a<=4):
                    break
                s+=a
                r=a
            else:
                if s==2:
                    return True
        return False
    @lru_cache(None)
    def choose(h,s,r,horizon):
        t=len(h); z=0 if not h else int(h[-1])
        obs=table[t][z]; q=F(obs['q'],8)
        choices=[]
        for a in action_order:
            e=s+a
            if not (abs(r-a)<=1 and 0<=e<=4 and terminal_safe(5-t,e,a)):
                continue
            draw=obs['demand']+5*max(a,0)+4*min(a,0)
            backup=max(draw-obs['cap'],0)
            v=(draw-backup)*obs['price']+backup*obs['backup']+abs(a)*obs['wear']
            if t+1==horizon:
                if horizon<6:
                    v+=slope*(2-e)
            else:
                v+=(1-q)*choose(h+'0',e,a,horizon)[0]+q*choose(h+'1',e,a,horizon)[0]
            choices.append((v,a))
        return min(choices,key=lambda x:x[0])
    policy={}
    # Stream each leaf in a different order; supply only its observed prefix at dispatch.
    for leaf in reversed(I.BITS):
        stock,previous=2,0
        for t in range(6):
            h=leaf[:t]
            a=choose(h,stock,previous,min(t+3,6))[1]
            if h in policy:
                assert policy[h]==a
            policy[h]=a
            stock+=a;previous=a
    return policy

def run(folder):
    raw=json.loads((folder/'records.json').read_text())
    checks={}
    for sh in raw:
        if sh['arm']!='shadow':
            continue
        table=sh['tables']
        idle={h:0 for h in sh['information']['issued']}
        policies={'idle':idle}
        for slope in (0,11,24,40):
            policies[str(slope)]=replay(table,slope)
        prices={k:I.audit(table,'policy',v) for k,v in policies.items()}
        assert prices=={k:F(v) for k,v in sh['portfolio_values'].items()}
        selected=min(prices,key=prices.get)
        assert selected==sh['selected'] and policies[selected]==sh['baseline_policy']
        assert all(I.audit(table,'policy',p)>=prices[selected] for p in policies.values())
        checks[sh['seed']]=selected
    return dict(designation='supplemental post-freeze reconstruction',families=len(checks),
                recovered_policy_values=len(checks)*5,recovered_selected_actions=len(checks)*63,
                winners=checks)
if __name__=='__main__':
    print(json.dumps(run(Path(__file__).parent/'results'),indent=2))
