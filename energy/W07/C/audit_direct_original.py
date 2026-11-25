"""Test the supplementary incumbent against exact upstream Pyomo rows and objective."""
from pathlib import Path
import json,gzip,shutil,tempfile
from independent_review import review
ROOT=Path(__file__).resolve().parent
def main():
    extra=ROOT/'postfreeze/direct_uc';w=review.read(extra/'witness.json.gz');r=review.read(extra/'summary.json')
    if w['primal'] is None:return dict(status='no schedule',rows=0)
    case=r['case'];src=ROOT/'uc_results'/case
    with tempfile.TemporaryDirectory() as tmp:
        dst=Path(tmp);target=dst/'uc_results'/case;target.mkdir(parents=True)
        shutil.copytree(ROOT/'inputs',dst/'inputs')
        cert=review.read(src/'certificate.json.gz');s=review.read(src/'summary.json')
        cert['primal']=w['primal'];s['U']=r['new_U']
        (target/'certificate.json.gz').write_bytes(gzip.compress(json.dumps(cert).encode()))
        (target/'summary.json').write_text(json.dumps(s))
        review.ROOT=dst
        return review.uc(dst/'inputs/2020-04-03.json',48)
if __name__=='__main__':
    import contextlib,sys
    with contextlib.redirect_stdout(sys.stderr):record=main()
    print(json.dumps(record,indent=2))
