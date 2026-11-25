import hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parent
def main():
    lock=json.loads((root/'freeze.json').read_bytes())
    for f,h in lock['code_sha256'].items():
        assert hashlib.sha256((root/f).read_bytes()).hexdigest()==h,f
    for row in json.loads((root/'sources.json').read_bytes()):
        b=(root/'inputs'/row['name']).read_bytes()
        assert len(b)==row['size'] and hashlib.sha1(f'blob {len(b)}\0'.encode()+b).hexdigest()==row['blob_sha1'],row
    print('All frozen code, model and six original input blob identities verified.')
if __name__=='__main__':main()
