# CU/DU instrumentation

Shared by Tasks 1–4. It exports native F1 context lifetimes and fresh repository
inventories, and can delay DU setup, modification, or release procedures.

## Run

After [setup](../README.md):

```text
python testbed/virtual/instrumentation/instrument.py run
python testbed/virtual/instrumentation/instrument.py run path/to/scenario.yaml --output traces/runs
python testbed/virtual/instrumentation/instrument.py check path/to/run/raw
```

## Settings

Place settings under `virtual.instrumentation` in a scenario:

| Setting | Value |
|---|---|
| `setup_ms`, `modification_ms`, `release_ms` | Integer delay, 0–2000 ms; default 0 |
| `arm_after_baseline` | Apply delays only after attachment and the baseline ping pass |
| `inactivity_s` | Optional CU inactivity timer, 5–120 seconds |

Hooks await native timers and leave the executor free. The measured wait is saved;
a hook that is never reached does not count as an applied perturbation. They control
the lab endpoint and do not imply that an ordinary UE has that capability.

## Evidence

Each run contains native CU/DU lifecycle logs, 250 ms repository inventories,
configuration, image/patch hashes, protocol captures, traffic probes, and reports.
The parser checks process/allocation epochs, F1 identifiers, the Linux boot ID,
time-namespace offsets, and capture continuity. It rejects stale images and traces.

The context check compares paired inventories after pending procedures and a
one-second settling interval. It requires a complete window, limits sample skew to
200 ms and gaps to 750 ms, and reports persistent differences as candidates.
These are experiment bounds, not 3GPP limits. Short or incomplete observations
remain inconclusive.

`no_inconsistency_observed` applies only to sampled F1 context presence.
`candidate_inconsistency` needs repetition, matched controls, and review before it
can become a confirmed finding. Packet loss alone is not a state mismatch.

Bearer/RLC/MAC tables, security state, E2 metrics, and pre-F1 random access are outside
this export. The hooks do not bypass native validation or force same-UE overlap.
