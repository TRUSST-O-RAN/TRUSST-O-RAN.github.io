# Results

No attack is confirmed.

## Latest: native context checks

[Nine-run campaign](https://github.com/TRUSST-O-RAN/thrust1-task1-cross-split-desynchronization/blob/main/results/context-validation-20261022/README.md), 2026-10-22:

| Condition | Repeats | Settled F1 state |
|---|---|---|
| Benign control | 3 | Matching contexts |
| Normal inactivity release | 3 | Both contexts removed |
| Release delayed past the CU timeout | 3 | Both contexts removed |

Delayed release changed cleanup order, but left no sampled context mismatch.
Traffic did not recover after either release condition. The pinned UE has an
unimplemented 5G Service Request path, so this does not establish a RAN fault.
Bearer and security consistency still need separate measurements.

## Earlier runs

- [Hook validation and native exports](https://github.com/TRUSST-O-RAN/thrust1-task1-cross-split-desynchronization/blob/main/results/instrumentation-20261022/README.md).
- [Successful connectivity baseline](https://github.com/TRUSST-O-RAN/thrust1-task1-cross-split-desynchronization/blob/main/results/benign-baseline-20261022-02/metadata.json).
- [Failed baseline, retained for diagnosis](https://github.com/TRUSST-O-RAN/thrust1-task1-cross-split-desynchronization/blob/main/results/benign-baseline-20261022-01/metadata.json).
- [Initial lifecycle observations](https://github.com/TRUSST-O-RAN/thrust1-task1-cross-split-desynchronization/blob/main/results/scenario-observations-20261022.json). The old
  `rlf` test affected idle LTE RRC and did not demonstrate NR link failure.

Small evidence sets and hashes are tracked here. Full logs and PCAPs stay local.
CU/DU stopped cleanly; core/UE can hit the stop timeout, so their log tails may
be incomplete. [Run the experiments](experiments.md).
