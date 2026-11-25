# Depth-sensitive wear on fixed W06 schedules

This post hoc revaluation uses the same eight path families at 7/30 days on the synthetic 12 MWh site. It includes 112 fixed scheduled-headroom trajectories (seven policy arms) and 48 hardened one-call trajectories (three arms). For each contract and path, exactly the same hourly dispatch, booked service, power availability, reserve offers, energy prices and closing stock are used as in the corresponding published comparison. All reserve costs are standing-service costs on the base trajectory. No controller was optimized or trained again.

**Replacement wear proxy.** Remove the original $8 per AC-throughput-MWh and second-block hourly surcharge. Apply whole-path rainflow counting to the existing SOC sequence, beginning and ending at 9 MWh. A depth of m stored MWh is normalized by 12 MWh of nominal capacity. The counter retains half cycles at both horizons and crosses midnight without resets. For half/full counts n and relative depth d, illustrative new cycling wear is the pack replacement price times the sum of n × 0.000524 × d^2.03. Xu et al. report this curve for specific NMC-based cylindrical cells (Eq. 24). Their example assumes $300/kWh pack replacement; $50, $150 and $300/kWh here probe price sensitivity, not current procurement prices. Temperature, calendar age, cell imbalance, prior stress and activation trajectories are unknown. This calculation does not estimate observed capacity fade or realized lifetime. Cycle curvature can favor a dispatch with the same throughput but shallower excursions. [Original equation and assumptions](https://arxiv.org/html/1707.04567#S5.SS1) · [Shi et al., cycle-counting algorithm and example](https://arxiv.org/pdf/1703.07968).

The two counters use a three-point stack and a separate four-point closed-loop elimination. Their half-cycle depth histograms agreed on all 160 trajectories. Each histogram also reconstructs total variation. Five small cases cover plateaus, monotone travel, a complete cycle, nested reversal and ranges following Shi et al. Table I. The model uses a finite record with residual half-cycle closure, fixed once for every policy. Histograms and operating cash before wear are saved for alternative price curves.

| Contract | Days | Continuation gain vs price rule at $50/$150/$300 per kWh, USD/day | Continuation gain vs three-scenario policy, USD/day |
|---|---:|---|---|
| Scheduled headroom | 7 | 55.76 / 50.26 / 42.02 | −0.91 / −7.32 / −16.94 |
| Scheduled headroom | 30 | 40.94 / 31.10 / 16.32 | −0.68 / −3.90 / −8.74 |
| One-call standby | 7 | 70.45 / 82.15 / 99.69 | 0.31 / −3.07 / −8.15 |
| One-call standby | 30 | 61.52 / 64.01 / 67.74 | −1.10 / −2.54 / −4.70 |

**Opportunity bound under the revised cost.** Let B(x) be nonwear operating cost, Wold(x) the former nonnegative wear, and Lold the certified offline optimum for the corresponding original contract. For any admissible path, old wear is no larger than M, the sum over hours of the maximum old wear of an allowed signed command under the observed power and mandatory power reservations. Thus B(x) ≥ Lold−M, and any nonnegative depth-wear cost preserves this lower bound. For a fixed reference schedule the new opportunity is at most B(ref)+R times the sum of n × 0.000524 × d² minus (Lold−M), using d^2.03 ≤ d². The code computes this ceiling as a rational number and rounds upward to the cent; displayed policy scores using d^2.03 use floating-point arithmetic. On 30-day paths at $150/kWh, these deliberately loose conservative ceilings against continuation average $687.24/day (scheduled-headroom contract) and $662.16/day (one-call contract). They do not resolve a practical saving. No existing offline optimizer discovered a rainflow-optimal path in this test.

**Replay.** Standard-library Python. From this folder, read the parent W06/E release and write a new results file in an empty output directory. The records are deterministic, including the input hash map. Before scoring, the design and core implementation were frozen in freeze.sha256. The wrapper was added for portable replay.

```sh
shasum -a 256 -c freeze.sha256
PYTHONDONTWRITEBYTECODE=1 python3 replay.py --source /path/to/W06/E --out /tmp/crgc-w06-rainflow-replay
cmp results.json /tmp/crgc-w06-rainflow-replay/results.json
```
