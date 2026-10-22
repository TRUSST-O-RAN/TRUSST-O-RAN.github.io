# Task 1.3 — E2 feedback-loop poisoning

Test whether misleading UE reports bias E2 measurements and near-real-time RIC decisions.

The virtual lab and shared CU/DU lifecycle instrumentation are available. The E2 attack is not implemented.

## Start

Follow the [virtual lab setup](virtual-setup.md). After building the images:

```text
python testbed/virtual/instrumentation/instrument.py run
```

Use context IDs and lifetime boundaries to join UE observations. E2/KPM, RIC, and xApp measurements are still required.

## Next

- Implement the task-specific signaling and observations.
- Run matched controls and measure effects on legitimate UEs.
- Record recovery and repeat across parameter settings and RAN implementations.

[Research requirements](plans/task-3.md) · [Shared instrumentation](instrumentation.md) · [Project documentation](https://trusst-o-ran.github.io/)

Run experiments only in an authorized lab. Code: [GPL-3.0](https://github.com/TRUSST-O-RAN/thrust1-task3-e2-feedback-loop-poisoning/blob/main/LICENSE).
