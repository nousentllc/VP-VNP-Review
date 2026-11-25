import hashlib,json,datetime,platform
from pathlib import Path
r=Path(__file__).resolve().parent
paths=[r/'opf.py',r/'structure.py',*sorted((r/'inputs').glob('*.m')),r.parent/'foundation/src/ac.py',r.parent/'foundation/results/C/development.json']
d=dict(frozen_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),platform=platform.platform(),threads=1,
       model='Exact AD IPOPT with W03-selected barrier strategy, fixed individual boxes and complete two-ended branch physics.',
       inputs='PGLib-OPF dc6be4b2f85ca0e776952ec22cbd4c22396ea5a3; typical and api 57,118,300,1354. CC BY 4.0.',
       arms=['full_dc','full_matched raw reconstructed generator warm start','all generator-bus pivots','original graph degree <=3 pivots'],
       design='5 repeats per cell, 12 s from parsing to physical validation. Rotate arm order; fresh processes; no claimed gain for misses. Report median within case, paired relative cost difference threshold 1e-5, practical speed criterion 10% median reduction at matched cost. Runs share a host with other single-threaded campaign jobs; no exclusive core allocation.',
       diagnostic='Post-clock once per case/arm: unweighted symmetric KKT structural graph including artificial diagonals, RCM order, exact symbolic Cholesky fill via ancestor reach. Also factor H_L+1e-6I,J;J.T,-1e-6I system (variable and constraint order as in code), estimate one-norm condition via SuperLU/COLAMD inverse operator. Diagnostic factorization is a proxy. Process RSS stamped before probes. Include cost across all timed construction/derivatives.',
       hypothesis='Does all-bus elimination raise validated feasible attainment or consistently reduce time at matched cost versus both full starts? Report every counterexample; no general speed claim on mixed cases.',
       sha256={str(p.relative_to(r.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})
(r/'freeze.json').write_text(json.dumps(d,indent=2))
