# Task 1.1 — Cross-split state desynchronization

Test whether CU and DU contexts or bearer resources remain inconsistent after F1 procedures finish.

Native CU/DU context exports, procedure delays, lifecycle controls, and sampled state checks are implemented. No attack is confirmed.

## Run

Set up the [virtual lab](virtual-setup.md), then run a control:

```text
python tools/scenario_runner.py scenarios/live/instrumented_control.yaml --backend virtual --trace-dir traces/runs
```

For software checks:

```text
python -m pip install -r requirements.txt
python -m pytest -q
```

## Current work

- Check context presence after setup, modification, and release.
- Test timeout and overlap cases against matched controls.
- Add actual bearer/resource and security observations.
- Replace the unsupported NR RLF trigger.
- Repeat useful cases and compare with a monolithic RAN.

## Read

- [Attack model](attack-model.md)
- [Experiments and result interpretation](experiments.md)
- [Results](validation.md)
- [Full research requirements](plans/task-1.md)
- [Project documentation](https://trusst-o-ran.github.io/)

Run experiments only in an authorized lab. Code: [GPL-3.0](https://github.com/TRUSST-O-RAN/thrust1-task1-cross-split-desynchronization/blob/main/LICENSE).
