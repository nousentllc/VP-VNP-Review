"""Recover development economics from the archived public tables for both pre-freeze panels."""
from pathlib import Path
from fractions import Fraction
import json,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import independent
import model

if __name__=='__main__':
    home=Path(__file__).resolve().parent
    result={}
    for version in ('initial','final'):
        records=json.loads((home/version/'records.json').read_text())
        checked=0
        for record in records:
            if record['arm']!='shadow':
                continue
            table=record['tables']
            if version=='initial':
                baseline,actions=model.rolling(table,3,11)
            else:
                candidates,_=model.portfolio(table)
                values={key:independent.audit(table,'policy',p) for key,p in candidates.items()}
                selected=min(values,key=values.get)
                baseline=values[selected];actions=candidates[selected]
            assert baseline==Fraction(record['baseline']) and actions==record['baseline_policy']
            for stage in record['stages']:
                assert Fraction(stage['value'])==independent.audit(table,stage['tier'])
            assert independent.audit(table,'policy',record['exact_policy'])==Fraction(record['stages'][-1]['value'])
            checked+=1
        result[version]=checked
    print(json.dumps({'archived_development_family_economics_reproduced':result}))
