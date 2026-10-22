# Task 1.2 — RU–DU buffer desynchronization

Test whether UE timing and HARQ behavior destabilize RU–DU buffers, scheduling, or retransmissions.

The virtual lab and shared CU/DU lifecycle instrumentation are available. The RU–DU attack is not implemented.

## Start

Follow the [virtual lab setup](virtual-setup.md). After building the images:

```text
python testbed/virtual/instrumentation/instrument.py run
```

Use context IDs and cleanup observations to track each UE. RU fronthaul, HARQ, and buffer measurements are still required.

## Next

- Implement the task-specific signaling and observations.
- Run matched controls and measure effects on legitimate UEs.
- Record recovery and repeat across parameter settings and RAN implementations.

[Research requirements](plans/task-2.md) · [Shared instrumentation](instrumentation.md) · [Project documentation](https://trusst-o-ran.github.io/)

Run experiments only in an authorized lab. Code: [GPL-3.0](https://github.com/TRUSST-O-RAN/thrust1-task2-ru-du-buffer-desynchronization/blob/main/LICENSE).
