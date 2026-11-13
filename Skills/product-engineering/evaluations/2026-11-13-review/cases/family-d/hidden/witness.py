#!/usr/bin/env python3
"""Finite pilot model. No clocks, biological inference, or delivery deadlines added."""
from dataclasses import dataclass, field
from itertools import permutations
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]

@dataclass
class Pilot:
    variant: str
    generation: dict = field(default_factory=lambda: {'J-A': 1, 'J-B': 1})
    # Sample S-A was drawn through the port before any actions in these traces.
    sample: tuple = ('J-A', 1)
    negatives: set = field(default_factory=set)
    gateway: tuple = (False, 0)
    consumer: tuple = (False, 0)
    pending: list = field(default_factory=list)
    leased: set = field(default_factory=set)

    def receive_negative(self):
        self.negatives.add(self.sample)
        if self.variant == 'p':
            self.project(True)

    def project(self, released):
        self.gateway = (released, self.gateway[1] + 1)
        self.pending.append(self.gateway)

    def reseal(self, jar):
        if jar in self.leased:
            return False
        self.generation[jar] += 1
        return True

    def handle_reseal_event(self):
        if self.variant == 'p':
            self.project(False)

    def deliver(self):
        # Arbitrary snapshot reordering is explicitly supported by the revision fence.
        for snapshot in reversed(self.pending):
            if snapshot[1] > self.consumer[1]:
                self.consumer = snapshot
        self.pending.clear()

    def reserve(self, jar):
        assert jar not in self.leased
        self.leased.add(jar)
        return (jar, self.generation[jar])

    def decide(self, coordinates, gateway_available=True):
        jar, generation = coordinates
        assert jar in self.leased and self.generation[jar] == generation
        if self.variant == 'p':
            return self.consumer[0]
        return gateway_available and coordinates in self.negatives

    def release(self, jar):
        self.leased.remove(jar)

    def ticket(self, jar):
        coordinates = self.reserve(jar)
        accepted = self.decide(coordinates)
        self.release(jar)
        return accepted, coordinates

    def authorized(self, coordinates):
        return coordinates in self.negatives


def run():
    # First verify document custody. The oracle records hashes of all review inputs.
    oracle = json.loads((ROOT / 'hidden/oracle.json').read_text())
    for name, expected in oracle['source_sha256'].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, name

    # Sibling jar: both jars are NB-71; only J-A generation 1 has negative evidence.
    p = Pilot('p')
    p.receive_negative()
    p.deliver()
    accepted, coordinates = p.ticket('J-B')
    assert accepted and not p.authorized(coordinates)

    # Previously eligible jar is resealed while its reset notification is delayed.
    p = Pilot('p')
    p.receive_negative()
    p.deliver()
    assert p.reseal('J-A')
    accepted, coordinates = p.ticket('J-A')
    assert accepted and coordinates == ('J-A', 2) and not p.authorized(coordinates)

    # Even with complete reset delivery, a delayed old sample resurrects clearance.
    p = Pilot('p')
    assert p.reseal('J-A')
    p.handle_reseal_event()
    p.deliver()
    assert not p.ticket('J-A')[0]
    p.receive_negative()
    p.deliver()
    accepted, coordinates = p.ticket('J-A')
    assert accepted and not p.authorized(coordinates)

    # Enumerate all orders of receipt, reseal, reseal-event, delivery and pick.
    # Reseal-event must occur after the physical reseal transaction. Other cross-
    # source delivery order is unspecified in the documents.
    schedules = 0
    accepted_q = 0
    for order in permutations(('receipt', 'reseal', 'event', 'deliver', 'pick')):
        if order.index('event') < order.index('reseal'):
            continue
        schedules += 1
        q = Pilot('q')
        for action in order:
            if action == 'receipt':
                q.receive_negative()
            elif action == 'reseal':
                assert q.reseal('J-A')
            elif action == 'event':
                q.handle_reseal_event()
            elif action == 'deliver':
                q.deliver()
            else:
                for jar in ('J-A', 'J-B'):
                    accepted, coordinates = q.ticket(jar)
                    assert not accepted or q.authorized(coordinates), (order, coordinates)
                    accepted_q += int(accepted)
    assert schedules == 60 and accepted_q > 0

    # Successful exact-coordinate lookup plus a lease protects the decision/draw.
    q = Pilot('q')
    q.receive_negative()
    coords = q.reserve('J-A')
    assert q.decide(coords)
    assert not q.reseal('J-A')
    assert q.generation['J-A'] == 1
    q.release('J-A')
    assert q.reseal('J-A')
    assert not q.ticket('J-A')[0]
    assert not q.ticket('J-B')[0]
    coords = q.reserve('J-B')
    assert not q.decide(coords, gateway_available=False)
    q.release('J-B')
    return {'source_hashes_verified': len(oracle['source_sha256']),
            'p_unauthorized_traces': 3, 'q_schedules_checked': schedules,
            'q_valid_tickets_observed': accepted_q,
            'q_reservation_and_unavailable_checks': 'passed',
            'status': 'passed'}

if __name__ == '__main__':
    print(json.dumps(run(), indent=2, sort_keys=True))
