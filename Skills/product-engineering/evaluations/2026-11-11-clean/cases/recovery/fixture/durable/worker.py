from .provider import OutcomeUnknown, DefinitelyRejected

class Worker:
    def __init__(self, store, provider, clock, lease_seconds=10):
        self.store, self.provider, self.clock = store, provider, clock
        self.lease_seconds = lease_seconds

    def run(self, op_id):
        result, row = self.store.claim(op_id, self.clock(), self.lease_seconds)
        if row is None:
            return result
        token = row['token']
        deadline = self.clock() + 30
        key = f"op:{op_id}:{token}"
        try:
            receipt = self.provider.execute(key, row['amount'], deadline)
        except OutcomeUnknown as exc:
            self.store.save(op_id, token, self.clock(), status='queued', error=str(exc))
            return 'queued'
        except DefinitelyRejected as exc:
            self.store.save(op_id, token, self.clock(), status='failed', error=str(exc))
            return 'failed'
        self.store.save(op_id, token, self.clock(), status='succeeded', dispatched=1,
                        deadline=deadline, receipt=receipt, error=None)
        return 'succeeded'
