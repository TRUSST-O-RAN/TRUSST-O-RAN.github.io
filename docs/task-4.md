# Task 1.4 — Random-access perturbations

Test whether incomplete random-access and RRC setup sequences leave resources allocated or disrupt other UEs.

The virtual lab and shared CU/DU lifecycle instrumentation are available. Selective random-access perturbations are not implemented.

## Start

Follow the [virtual lab setup](virtual-setup.md). After building the images:

```text
python testbed/virtual/instrumentation/instrument.py run
```

Use allocation and cleanup exports to track established F1 contexts. Earlier MSG1–MSG5 events and selective UE controls are still required.

## Next

- Implement the task-specific signaling and observations.
- Run matched controls and measure effects on legitimate UEs.
- Record recovery and repeat across parameter settings and RAN implementations.

[Research requirements](plans/task-4.md) · [Shared instrumentation](instrumentation.md) · [Project documentation](https://trusst-o-ran.github.io/)

Run experiments only in an authorized lab. Code: [GPL-3.0](https://github.com/TRUSST-O-RAN/thrust1-task4-random-access-perturbations/blob/main/LICENSE).
