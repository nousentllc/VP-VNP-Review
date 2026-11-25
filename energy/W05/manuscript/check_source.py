"""Verify the exported source against the ordered block hashes and audit literal LaTeX keys."""
import argparse, collections, hashlib, json, re
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def inspect(source,order):
    s=source.read_bytes().decode('utf-8');o=json.loads(order.read_text())
    assert hashlib.sha256(s.encode()).hexdigest()==o['source_sha256']
    pos=0
    for j,block in enumerate(o['blocks']):
        if j:
            assert s[pos]=='\n'
            pos+=1
        n=block['characters'];chunk=s[pos:pos+n];pos+=n
        assert hashlib.sha256(chunk.encode()).hexdigest()==block['source_sha256']
    assert pos==len(s)
    clean=re.sub(r'(?<!\\)%[^\n]*','',s)
    def keys(cmd):
        return [t.strip() for z in re.findall(r'\\(?:'+cmd+r')\{([^{}]+)\}',clean) for t in z.split(',')]
    bib=keys('bibitem');cited=keys('cite');labels=keys('label');refs=keys('ref|eqref|pageref')
    return dict(source_bytes=source.stat().st_size,lines=len(s.splitlines()),characters=len(s),blocks=len(o['blocks']),
        bibitems=len(bib),cited_distinct=len(set(cited)),cited_missing=sorted(set(cited)-set(bib)),uncited=sorted(set(bib)-set(cited)),
        duplicate_bib=[k for k,n in collections.Counter(bib).items() if n>1],duplicate_labels=[k for k,n in collections.Counter(labels).items() if n>1],
        labels=len(labels),ref_keys=len(set(refs)),refs_missing=sorted(set(refs)-set(labels)))
if __name__=='__main__':
    print(json.dumps(inspect(ROOT/'CRGC_Whitepaper_v0.4.tex',ROOT/'source_order.json'),indent=2))
