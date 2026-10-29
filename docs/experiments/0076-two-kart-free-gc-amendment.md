# Free qualification amendment before any paid multiplayer calls

Four original full free duels finished cleanly and passed replay audits. The
170.1 s neutral test then failed the unchanged 100 ms maximum-lateness limit:
127.327 ms late at tick 9435 (157.25 s), despite .908 ms total drift and
1.515 ms p95 lateness. The diagnostic log records a generation-2 garbage
collection from monotonic ns 135998451051099 to 135998587048051: 135.997 ms
wall / 135.968 ms process CPU, zero objects collected. The next wake was
135998587437448. This directly identifies a local collection pause; no model
request was involved.

The private multiplayer worker now collects before starting and disables cyclic
collection for its bounded process lifetime. Ordinary reference counting remains
active. Each duel gets a fresh process, has a maximum 600 s duration, and the
worker exits after collection. Result metadata records actual cyclic-GC status
and maximum resident memory. The inline diagnostic runtime and solo worker
retain their original collection behavior. No physics equation, collision rule,
model prompt, native control, race configuration or timing limit changed.

All original source bytes match their recorded hashes and are retained under
`artifacts/two-kart-session-v1/free-source-before-gc/`. Original registration,
helper and checks are retained separately; all four controls and the failed
long recording are under `clock-before-gc/`. The first registration is also
versioned as `0076-two-kart-original-free-registration.json`. The orchestration
helper additionally saves long-clock recordings before assertions, preserving
evidence if a later qualification fails.

The complete four-control plus long-clock gate must be repeated on the new
source and fresh server binding. No paid multiplayer call had occurred at this
amendment. The global ledger remains 79,634 requests / 282,185,152 tokens /
$9.149239028003063 with all 70 uncertainties, no pending reservation, and the
user-authorized $20 / 100,000-request / 500-million-token caps.
