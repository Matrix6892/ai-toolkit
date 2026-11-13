#!/usr/bin/env python3
"""Executable interpretation of the supplied contracts; no external dependencies."""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent

def half(value):
    return value // 2

def award(estimate):
    return min(half(estimate), 100000)

def required(estimate, completion):
    return min(award(estimate), half(completion))

def packet_p(estimate, completion):
    # 03 lines 5-11: estimate is replaced when completion is accepted.
    eligible_cost = estimate
    issued = award(eligible_cost)
    eligible_cost = completion
    # 03 line 14 and 04 lines 4-5: support is derived from the current field.
    derived_support = award(eligible_cost)
    return issued, min(half(eligible_cost), derived_support)

def packet_q(estimate, completion):
    # 03 lines 4-15: typed immutable facts preserve the estimate.
    facts = {"ESTIMATE": estimate, "COMPLETION": completion}
    issued = award(facts["ESTIMATE"])
    return issued, min(half(facts["COMPLETION"]), award(facts["ESTIMATE"]))

def main():
    # Anchor each interpretation to verbatim documentary statements.
    anchors = {
      "packet-p/03-data-design.md": [
        "Принятие акта заменяет eligible_cost проверенной стоимостью акта.",
        "Для DECIDED и COMPLETION_ACCEPTED derived_support = min(eligible_cost / 2, 100000)."],
      "packet-q/03-data-design.md": [
        "Принятые факты неизменяемы; source_id устраняет повторную доставку.",
        "Для DECIDED и COMPLETION_ACCEPTED derived_support = min(ESTIMATE.eligible_cost / 2, 100000)."],
      "packet-p/01-programme.md": [
        "Фактическая выплата равна меньшему из суммы поддержки и 50% допустимых фактических затрат."]
    }
    for name, snippets in anchors.items():
        source = (ROOT / name).read_text()
        for snippet in snippets:
            assert snippet in source, (name, snippet)
    estimate, completion = 100000, 160000
    issued_p, paid_p = packet_p(estimate, completion)
    issued_q, paid_q = packet_q(estimate, completion)
    assert issued_p == issued_q == 50000
    assert paid_p == 80000 > issued_p
    assert required(estimate, completion) == paid_q == 50000
    checked, failures_p = 0, 0
    # Permitted estimate/actual amounts, including zero, decline, growth and cap.
    values = [0, 1, 20000, 60000, 100000, 160000, 200000, 300000]
    for estimate in values:
        for completion in values:
            expected = required(estimate, completion)
            assert packet_q(estimate, completion)[1] == expected
            failures_p += packet_p(estimate, completion)[1] != expected
            checked += 1
    assert failures_p > 0
    print(json.dumps({"counterexample": {"estimate": 100000, "completion": 160000,
      "issued": issued_p, "packet_p_paid": paid_p, "packet_q_paid": paid_q},
      "checked_scenarios": checked, "packet_p_violations": failures_p,
      "packet_q_violations": 0}, ensure_ascii=False))

if __name__ == "__main__":
    main()
