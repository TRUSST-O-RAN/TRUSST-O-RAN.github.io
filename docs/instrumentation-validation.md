# Native instrumentation validation, 2026-10-22

Five isolated live runs built on the pinned OCUDU overlay and exported native
CU/DU F1 context state. [summary.json](https://github.com/TRUSST-O-RAN/thrust1-task1-cross-split-desynchronization/blob/main/results/instrumentation-20261022/summary.json) contains the measured
timings, procedure coverage, probe outcomes, and container exit codes.

| Condition | Requested hook | Measured hook wait | Follow-up traffic |
|---|---|---|---|
| Instrumented control | All zero | Setup 0.742 ms; modification 0.673 ms | 3/3 replies |
| Setup delay | 100 ms | 108.015 ms | 3/3 replies |
| Modification delay | 100 ms | 108.421 ms | 3/3 replies |
| Inactivity release control | Release 0 ms | 0.524 ms | Recovery not observed |
| Inactivity release delay | Release 100 ms | 108.802 ms | Recovery not observed |

All five runs attached and passed their initial 3/3 tunnel probes. The
release conditions both used an eight-second inactivity timer. Both completed
correlated setup, modification, and release procedures and exported deletion
of both CU and DU F1 contexts. Neither recovered traffic during the bounded
post-release probes. This observation does not establish an orphaned F1
context or a hook-caused recovery failure. The underlying recovery behavior
still needs diagnosis and repetition.

The other three conditions correlated setup and modification. Native records
were readable with no sequence gaps or ambiguous identifier pairs. Every
original archive SHA-256 entry was verified, all six collection commands
returned zero, and clean pinned source checks passed. All three CU/DU protocol
PCAPs in each archive contained complete records. CU/DU exited 0; core/UE
reached the stop timeout and exited 137, so their log tails may be incomplete.

This directory retains the exact native JSONL exports, original state reports,
and provenance for review. Each provenance file records their hashes, the
captured analyzer hash, image fingerprint, and original archive metadata hash.
Complete logs, PCAPs, backend/instrumentation source snapshots, configurations,
and individual traffic probes remain in local ignored archives at
`traces/live-task1-instrumented/virtual-RUN-ID/`. This tracked subset alone
does not replace those full archives.

These are instrumentation validation observations. All attack outcomes remain
`inconclusive`, and `success` is false. Limited F1 context coverage does not
complete the broader white-box or attack evaluation deliverables. See the
[instrumentation guide](instrumentation.md).
