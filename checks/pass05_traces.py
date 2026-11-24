"""Enumerate the pinned pointer-machine rules on four small canonical programs."""

import json
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Rule:
    source: str
    target: str
    load_kind: str
    load_register: int
    allocation: str
    fields: tuple
    registers: tuple
    read: tuple = ()
    weight: int = 1


def read_rule(expression, read=(), weight=1):
    tokens = expression.split()
    assert len(tokens) == 13 and tokens[0] == "rl", expression
    fields = tuple(map(int, tokens[6:9]))
    registers = (0, *map(int, tokens[9:13]))
    return Rule(tokens[1], tokens[2], tokens[3], int(tokens[4]), tokens[5],
                fields, registers, read, weight)


def transition_table():
    """Read ruleA from the primary source. Specialize the four name cases to {[]: -1}."""
    file = Path(__file__).resolve().parents[1] / "primary/vp-vnp/Nc/Uni/Rules.lean"
    source = file.read_text()
    table = source.split("def ruleA ", 1)[1].split("/-- The rules. -/", 1)[0]
    rules = []
    for line in table.splitlines():
        if "=>" not in line:
            continue
        left, expression = (part.strip() for part in line.split("=>"))
        label = left.split()[1]
        bits = [False, True] if left.endswith(" b") else [None]
        indices = range(10) if label == ".dc" else [None]
        for bit in bits:
            for index in indices:
                active = expression
                read = ()
                if active.startswith("if b then"):
                    yes, no = active.removeprefix("if b then ").split(" else ")
                    active = yes if bit else no
                if active.startswith("{"):
                    active, suffix = active.split(" : RD A N) with rd := some ")
                    active = active.removeprefix("{ (")
                    assert suffix in ("true }", "false }")
                    read = (int(suffix == "true }"),)
                if bit is not None:
                    active = active.replace("(kb b)", ".C" if bit else ".N")
                if index is not None:
                    active = active.replace("(.D j.castSucc)", f".D{index}")
                    active = active.replace("(.D j.succ)", f".D{index + 1}")
                active = re.sub(r"\(\.D (\d+)\)", r".D\1", active)
                rules.append(read_rule(active, read))
    # In rule (lines 113–119), the only supported prefix is []. There are no
    # prefix-extension rules. Keep the numeric columns directly from the source.
    for original, simple, weight in [
        ("rl .R (.TH ⟨[], u.2⟩) .TH", "rl .R .TH0 .TH", 1),
        ("rl (.TH p) .R .N", "rl .TH0 .R .N", -1),
        ("rl (.TH p) (.TB p) .C", "rl .TH0 .TB0 .C", 1),
    ]:
        line, = (line for line in source.splitlines() if original in line)
        numbers = line.split(original, 1)[1].split(" : RD", 1)[0].strip()
        rules.append(read_rule(simple + " " + numbers, weight=weight))
    return rules


def unary(number):
    tag = None
    for _ in range(number):
        tag = (None, tag)
    return tag


def code(tag, body=None):
    return (unary(tag), body)


def preorder(tree):
    return (0,) if tree is None else (1,) + preorder(tree[0]) + preorder(tree[1])


def evaluate_pointer(rules, word, guard):
    """Fire/nxt/Seq in Nc/Uni/PM.lean. Heap indices are the fresh addresses."""
    states = [(".S0", (0,) * 5, ((".N", (0, 0, 0)),), 0, 1, 0)]
    accepted = []
    stuck = []
    while states:
        mode, registers, heap, cursor, coefficient, steps = states.pop()
        if mode == ".Z" and cursor == len(word):
            accepted.append({"weight": coefficient, "steps": steps})
            continue
        # Fail the check on truncation, including a hypothetical long dead branch.
        assert steps < guard, "the enumeration did not exhaust the state tree"
        successors = []
        for rule in rules:
            if rule.source != mode or word[cursor:cursor + len(rule.read)] != rule.read:
                continue
            kind, fields = heap[registers[rule.load_register]]
            if kind != rule.load_kind:
                continue
            env = registers + fields + (len(heap),)
            new_record = (rule.allocation, tuple(env[i] for i in rule.fields))
            new_registers = tuple(env[i] for i in rule.registers)
            successors.append((rule.target, new_registers, heap + (new_record,),
                               cursor + len(rule.read), coefficient * rule.weight, steps + 1))
        if not successors:
            stuck.append({"mode": mode, "steps": steps})
        states.extend(successors)
    return {"accepting_traces": accepted, "stuck_branches": stuck,
            "value": sum(trace["weight"] for trace in accepted)}


def check():
    # NS1/Machine.lean, Fm.code and Ev. The one-bit false name is cons nil nil.
    quote_nil = code(0)
    supported = code(9, quote_nil)
    guess = code(7)
    cases = [
        ("absent_weight", code(9, code(0, (None, None))), [0], [], 2),
        ("supported_weight", supported, [-1], [-1], 2),
        ("duplicate_output", code(2, guess), [1, 1], [1, 1], 2),
        ("cancellation", code(5, (guess, (supported, quote_nil))), [1, -1], [1, -1], 4),
    ]
    rules = transition_table()
    results = {}
    for name, program, source_weights, expected_pointer_weights, tau in cases:
        word = preorder((program, None))
        # The cost estimate in Bounds.lean includes the longest name, zero here.
        bound = 3 * len(word) + 40 * tau + 10
        result = evaluate_pointer(rules, word, 4 * bound)
        weights = [trace["weight"] for trace in result["accepting_traces"]]
        assert sorted(weights) == sorted(expected_pointer_weights)
        assert result["value"] == sum(source_weights)
        assert all(trace["steps"] <= bound for trace in result["accepting_traces"])
        if name == "absent_weight":
            assert [s["mode"] for s in result["stuck_branches"]] == [".TB0"]
        result.update(source_weights=source_weights, input_nodes=len(word),
                      source_accepting_cost_bound=tau, pointer_step_bound=bound)
        results[name] = result
    return results


if __name__ == "__main__":
    print(json.dumps(check(), indent=2))
