"""Replay two exact, synthetic controls with Python 3.9+ and its standard library.

Run `python3 replay_controls.py` to print a deterministic JSON record.
Power is constant over each one-hour period. All costs are illustrative.
"""

import json
from fractions import Fraction
from itertools import product


def evaluate_schedule(schedule, initial, capacity, power_limit, efficiency, required_import):
    """Evaluate grid, state, relaxed mode and per-device physical constraints separately."""
    if len(schedule) != len(required_import) or any(len(period) != len(initial) for period in schedule):
        raise ValueError('Each required hour and battery must have a corresponding action.')
    soc = list(initial)
    imports = []
    throughput = Fraction(0)
    meets_state_limits = True
    meets_relaxed_power_bounds = True
    simultaneous = []
    for t, devices in enumerate(schedule, start=1):
        grid_import = Fraction(0)
        for i, (charge, discharge, mode) in enumerate(devices):
            if not (0 <= mode <= 1 and 0 <= charge <= power_limit * mode
                    and 0 <= discharge <= power_limit * (1 - mode)):
                meets_relaxed_power_bounds = False
            if charge > 0 and discharge > 0:
                simultaneous.append([t, i + 1])
            soc[i] += efficiency * charge - discharge / efficiency
            meets_state_limits = meets_state_limits and 0 <= soc[i] <= capacity
            grid_import += charge - discharge
            throughput += charge + discharge
        imports.append(grid_import)

    relaxed_feasible = (meets_state_limits and meets_relaxed_power_bounds
                        and tuple(soc) == initial and tuple(imports) == required_import)
    return {
        'grid_import_by_hour': list(map(str, imports)),
        'terminal_soc_by_device': list(map(str, soc)),
        'linear_throughput_cost_at_unit_price': str(throughput),
        'satisfies_relaxation': relaxed_feasible,
        'simultaneous_device_hours_as_hour_device': simultaneous,
        'physically_admissible_powers': relaxed_feasible and not simultaneous,
    }


def check_schedule_averaging():
    """Average two binary-feasible schedules and check the resulting power instructions."""
    charging = (Fraction(1), Fraction(0), Fraction(1))
    discharging = (Fraction(0), Fraction(16, 25), Fraction(0))
    first = ((charging, discharging), (discharging, charging))
    second = (first[1], first[0])
    average = [
        [tuple((x + y) / 2 for x, y in zip(action_a, action_b))
         for action_a, action_b in zip(period_a, period_b)]
        for period_a, period_b in zip(first, second)
    ]
    initial = (Fraction(3, 2), Fraction(3, 2))
    records = {
        name: evaluate_schedule(schedule, initial, 3, 1, Fraction(4, 5), (Fraction(9, 25),) * 2)
        for name, schedule in [('original', first), ('relabeling', second), ('average', average)]
    }
    if not all(records[name]['physically_admissible_powers'] for name in ['original', 'relabeling']):
        raise ValueError('The two positive controls must pass all device and grid checks.')
    if not records['average']['satisfies_relaxation'] or records['average']['physically_admissible_powers']:
        raise ValueError('The average must pass the LP and fail physical admissibility.')
    if records['average']['simultaneous_device_hours_as_hour_device'] != [[1, 1], [1, 2], [2, 1], [2, 2]]:
        raise ValueError('All four device-hours must exhibit simultaneous charge and discharge.')
    if {record['linear_throughput_cost_at_unit_price'] for record in records.values()} != {'82/25'}:
        raise ValueError('The three schedules must have the same exact throughput cost.')
    return records


def check_labeled_endpoints():
    """Enumerate all terminal states in a one-period, two-battery ideal model, k=1."""
    initial = (1, 0)
    target = (0, 1)
    outcomes = {}
    for end in product(range(2), repeat=2):
        moves = [after - before for before, after in zip(initial, end)]
        if sum(moves) == 0 and all(abs(move) <= 1 for move in moves):
            outcomes[end] = sum(abs(move) for move in moves)
    records = {
        'aggregate_zero_movement_cost': abs(sum(target) - sum(initial)),
        'minimum_cost_with_fixed_swapped_labels': outcomes[target],
        'minimum_cost_with_fixed_identical_endpoints': outcomes[initial],
        'minimum_cost_with_endpoint_permutations_allowed': min(outcomes.values()),
    }
    if (records['aggregate_zero_movement_cost'] != 0
            or records['minimum_cost_with_fixed_swapped_labels'] != 2
            or records['minimum_cost_with_fixed_identical_endpoints'] != 0
            or records['minimum_cost_with_endpoint_permutations_allowed'] != 0):
        raise ValueError('The endpoint control did not reproduce the expected labeled costs.')
    return records


def main():
    results = {
        'scope': 'Exact synthetic handoff controls, separate from the W03 campaign',
        'schedule_averaging': check_schedule_averaging(),
        'endpoint_labels': check_labeled_endpoints(),
    }
    print(json.dumps(results, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
