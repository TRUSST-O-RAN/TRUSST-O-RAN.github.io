# Native CU/DU instrumentation

Task 1 now provides an optional OCUDU source patch and image overlay under
[`testbed/virtual/task1`](instrumentation.md). It adds asynchronous
DU procedure delay hooks and native F1 context exports while keeping the
shared portable lab and pinned source checkout unchanged.

The hooks cover UE Context Setup, Modification, and Release. Per-run delays
are bounded to 0–2000 ms and use OCUDU's asynchronous timers. Native exports
record actual context creation/deletion, CU/DU F1 identifiers, allocation and
process epochs, release flags, DU RRC configuration state, and procedure
boundaries. The runner checks the image fingerprint and retains effective
configuration, instrumentation sources, native traces, and measured hook waits.

The native schema is `trusst.f1-state.v1`, separate from the older generic
latest-value checker. Its coverage analyzer joins only complete serialized
procedure chains with unambiguous identifiers. It rejects missing, stale,
corrupt, or ambiguous evidence; no console message becomes a synthetic state.
CU and DU native timestamps use one Docker Linux kernel clock. Windows host
controller monotonic timestamps are a separate domain.

See the [build, run, schema, and interpretation guide](instrumentation.md)
for the instrumented control and positive setup/modification/release hook checks.
The release check uses normal UE inactivity followed by a recovery traffic probe.

The [five live validation runs](instrumentation-validation.md)
measured 108.015 ms for the 100 ms setup hook, 108.421 ms for modification,
and 108.802 ms for release. Control/setup/modification retained traffic.
Both the zero-delay and delayed inactivity release completed F1 cleanup but
failed to recover traffic during the bounded observation; the cause remains
unresolved. These observations do not establish an attack or orphaned F1 context.

`white_box_available` reports limited F1 context observation coverage. Actual
DRB/RLC/MAC tables, PDCP/security state, F1 association epochs, cross-host clock
bounds, and settled-state invariants remain to be implemented. These results
cannot yet establish a cross-split inconsistency or attack success rate.
