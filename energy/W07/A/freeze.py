"""Lock the generator, contract, checkers and predeclared arms before generation."""
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import json
p=Path(__file__).resolve().parent
names=['design.json','model.py','native.py','independent.py','run.py','freeze.py','verify.py','requirements.txt']
with (p/'freeze.json').open('x') as f:
    json.dump(dict(frozen_utc=datetime.now(timezone.utc).isoformat(),
                   files={q:sha256((p/q).read_bytes()).hexdigest() for q in names},
                   holdout_status='unopened; development and W06 regression only'),
              f,indent=2)
    f.write('\n')
