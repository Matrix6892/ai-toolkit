# Museum rehearsal review: release packet
Owner: Touring Content team; architecture decision draft, 12 November 2026.
A coordinator prepares a release packet before printing a museum's audio tour.
The packet is a ZIP containing preview files and a review ledger in CSV.
Reviewers create findings against a specific immutable preview, not a tour name.
Each finding records its severity, disposition, author and authoritative event number.
The ledger must show the effective state of every finding at its captured cutoff, accounting for all review changes committed through that cutoff.
This is a state snapshot, not a change-history export: a closed finding appears once in its final eligible state.
Effective states must exclude changes committed after that cutoff, even if creation takes minutes.
An unresolved blocking finding must appear in the ledger and mark its preview blocked.
A missing finding is not equivalent to an open finding; it can cause incorrect printing.
The cutoff is the museum event-log head captured by the server when accepting Export.
The response gives that cutoff and a job ID; the user may continue reviewing afterward.
A job may wait while its cutoff becomes readable; no completion deadline is promised.
A failed dependency should leave the job pending or failed, never a partial success.
A completed job is immutable and downloadable again with identical bytes for 90 days.
The same application has a live activity strip: newest processed review and rough counts.
That strip is a convenience cue and may skip intermediate states or lag briefly.
Reviewers use the saved finding detail, not the strip, to confirm their own edit.
Anonymous trend reports count activity; exact historical evidence is not their purpose.
The release packet is the authoritative record for the printing coordinator.
