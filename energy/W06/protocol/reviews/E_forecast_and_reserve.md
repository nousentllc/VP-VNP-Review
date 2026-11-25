# Independent W06-E access and reserve review

All 77,088 positive-lead rows on the 16 confirmatory 7/30-day paths were independently reconstructed using the published clock, current price and power availability, and job bookings already issued at or before the decision. All matched the archived H12 issues. Current-hour rows also matched observations. High and low jobs are announced two and five hours ahead and become fixed service at their booked slots. Later arrivals enter forecasts through a deterministic default. The controllers receive the finite horizon length and H12 issue, and dispatch.py reads the length of the realized array for the known ending time. Frozen scalar price/tail choices use two separate development seeds. The study's gate uses offline holdout headroom to decide whether to attempt the prespecified policy test. The compared actions do not receive the offline schedules. The 7- and 30-day paths within a seed share random streams, so eight seed blocks support the sign analysis, not 16 independent replicates.

The forecast has a publicly guaranteed outage-free last 16 hours. The terminal guard uses this assurance. A power failure during that interval, delayed job notifications or an unexpected termination would change the contract. Primary action trajectories agree on hourly booked service, the modeled non-deployment power headroom and closing inventory. The plant does not require stock or upper capacity to sustain an activated mandatory reservation for a full hour. The registered assertions therefore establish the scheduled capacity contract. Online service reliability under activation remains open.

We tested this distinction retrospectively. For each positive mandatory up/down booking, perturb the scheduled storage command q by the entire corresponding booking for exactly one hour, leaving its starting SOC unchanged. Count inventory or accessibility violations only. The test assumes the reserve is sustained for an hour in the model's own storage-block units. It omits all grid, ramp, subsequent recovery, event probabilities and optional bid deployment. Each hour is a separate perturbation, without propagating the modified state. The percentages are stress exposure frequencies, not probabilities of failure.

| Policy | Up inventory failures / 1,655 booked path-hours | Down inventory failures / 1,629 booked path-hours |
|---|---:|---:|
| Fill | 0 | 1,349 |
| Price-aware rule | 473 | 452 |
| H6 zero-tail | 330 | 0 |
| H12 zero-tail | 245 | 37 |
| H12 continuation | 137 | 133 |
| H12 constant $50 | 222 | 49 |
| Three-scenario H12 | 136 | 123 |

A one-hour activation would encounter fewer inventory conflicts for continuation than for the price-aware rule, but more downward conflicts than for H12 zero-tail. These facts do not certify risk noninferiority or net value under an activated contract. A follow-up can put reserve activation states, power, deliverable energy, recovery, and nonanticipativity into both the offline bounds and online policies.

## Recompute the one-hour stress counts

From the W06 directory, run the following script with Python 3. Its only inputs are the released E inputs and action traces.

```python
import gzip
import json
from collections import Counter, defaultdict
from pathlib import Path

def inventory_stress(track):
    def read(path):
        return json.loads(gzip.decompress(path.read_bytes()))
    counts = defaultdict(Counter)
    for path in sorted((track / "inputs").glob("[0-9]*.json.gz")):
        scenarios = read(path)
        results = track / "results"
        policies = {**read(results / ("online_" + path.name)),
                    **read(results / ("supplement_" + path.name)),
                    "price": read(results / ("baseline_" + path.name))["price"]}
        for policy, plan in policies.items():
            soc = 9
            for action, row in zip(plan["actions"], scenarios["actual"], strict=True):
                command, next_soc = action[:2]
                assert soc + command == next_soc
                for i, sign, side in [(6, -1, "up"), (7, 1, "down")]:
                    if row[i] == 0:
                        continue
                    counts[policy][side + "_hours"] += 1
                    activated = command + sign * row[i]
                    final = soc + activated
                    if not 2 <= final <= 11 or (activated < 0 and final < row[5]):
                        counts[policy][side + "_stock_failures"] += 1
                soc = next_soc
    return {key: dict(count) for key, count in counts.items()}

print(inventory_stress(Path("E")))
```
