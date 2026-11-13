#!/usr/bin/env python3
"""Small executable semantics of the documents; no external services required."""
import json
from itertools import permutations
from pathlib import Path

EVENTS = {
    1: {'guide': 'A', 'digest': 'preview-A', 'finding': 'F1', 'severity': 'blocking', 'state': 'open'},
    2: {'guide': 'B', 'digest': 'preview-B', 'finding': 'F2', 'severity': 'note', 'state': 'open'},
    3: {'guide': 'A', 'digest': 'preview-A', 'finding': 'F1', 'severity': 'blocking', 'state': 'closed'},
}

class Projection:
    def __init__(self, policy):
        self.policy, self.rows, self.position = policy, {}, 0

    def commit_callback(self, number):
        # Models one serialized atomic transaction (insert + position update).
        payload = EVENTS[number]
        if number in self.rows:
            assert self.rows[number] == payload
            return
        self.rows[number] = dict(payload)
        if self.policy == 'highest':
            self.position = max(self.position, number)
        else:
            while self.position + 1 in self.rows:
                self.position += 1

    def read_packet(self, cutoff):
        # One primary snapshot, after checking readiness in that same snapshot.
        if self.position < cutoff:
            return None
        effective = {}
        for number, event in sorted(self.rows.items()):
            if number <= cutoff:
                effective[event['finding']] = event
        blocked = sorted({e['digest'] for e in effective.values()
                          if e['severity'] == 'blocking' and e['state'] == 'open'})
        return {'findings': sorted(effective), 'blocked': blocked,
                'states': {key: event['state'] for key, event in sorted(effective.items())}}


def expected(cutoff):
    # The source contract defines truth by commit number, independently of callback order.
    effective = {}
    for number in range(1, cutoff + 1):
        effective[EVENTS[number]['finding']] = EVENTS[number]
    return {'findings': sorted(effective),
            'states': {key: event['state'] for key, event in sorted(effective.items())},
            'blocked': sorted({e['digest'] for e in effective.values()
                               if e['severity'] == 'blocking' and e['state'] == 'open'})}


def main():
    q, p = Projection('highest'), Projection('prefix')
    # Delivery is 1,2; two worker callbacks then finish in order 2,1.
    # Export acceptance captured head 2 before these completions.
    for projection in (q, p):
        projection.commit_callback(2)
    observed = q.read_packet(2)
    assert observed == {'findings': ['F2'], 'blocked': [], 'states': {'F2': 'open'}}
    assert observed != expected(2), 'Packet q must violate the required cutoff result'
    assert p.read_packet(2) is None, 'Packet p must wait for the missing earlier callback'
    for projection in (q, p):
        projection.commit_callback(1)
        projection.commit_callback(2)  # Broker redelivery is harmless.
        projection.commit_callback(3)  # A later close must not affect cutoff 2.
        assert projection.read_packet(2) == expected(2)
        assert projection.read_packet(3) == expected(3)
        assert projection.read_packet(3)['states']['F1'] == 'closed'
        assert projection.read_packet(3)['blocked'] == []
    # Every completion order of three delivered callbacks is legal under the broker contract.
    # Check each intermediate observation, including early completion of future event 3.
    admitted = 0
    for order in permutations((1, 2, 3)):
        projection = Projection('prefix')
        for number in order:
            projection.commit_callback(number)
            for cutoff in (1, 2, 3):
                result = projection.read_packet(cutoff)
                if result is not None:
                    admitted += 1
                    assert result == expected(cutoff), (order, number, cutoff, result)
        assert projection.read_packet(2) == expected(2)
    print(json.dumps({'packet_q_counterexample': observed, 'required': expected(2),
                      'packet_p_orders_checked': 6, 'cutoffs_checked': [1, 2, 3],
                      'snapshot_close_case': p.read_packet(3), 'packet_p_admitted_snapshots': admitted,
                      'assertions': 'passed'}, sort_keys=True))

if __name__ == '__main__':
    main()
