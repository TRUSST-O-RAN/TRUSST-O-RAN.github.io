# Experiments

Build the [virtual lab](virtual-setup.md) first. Run scenarios with:

```text
python tools/scenario_runner.py scenarios/live/instrumented_control.yaml --backend virtual --trace-dir traces/runs
python tools/scenario_runner.py scenarios/live/release_timeout.yaml --backend virtual --trace-dir traces/runs
```

The first is a benign control. The second attaches normally, arms a 1500 ms
release delay, waits for inactivity release, and checks settled CU/DU state.
The delay exceeds the pinned CU's default 1000 ms F1 procedure timeout.

Other files in `scenarios/live/` cover setup/modification delays and single-UE
restart. `scenarios/proposed/` holds unimplemented plans; use `--dry-run` for those.

The pinned UE's `rlf` command acts on LTE RRC. Its earlier trace explicitly
reports that the failure was ignored in LTE idle state; it did not validate NR
RLF. That live action is now blocked. NR inactivity recovery is also limited:
`nas_5g::start_service_request()` logs the request but has no implementation.
Failed post-release traffic therefore does not establish a RAN cleanup defect.

## Read a run

- `result.json`: execution and traffic outcome; attack status stays separate.
- `raw/cycle-*-context-check.json`: settled F1 presence check.
- `raw/CU-inventory.jsonl`, `DU-inventory.jsonl`: fresh native repositories.
- `raw/*-state.jsonl`: lifecycle, procedure, and hook events.
- `metadata.json`: captured file hashes and collection exit codes.

Recheck the captured state window:

```text
python testbed/virtual/instrumentation/instrument.py check path/to/run/raw
```

A zero runner exit code means execution completed. A sampled state pass covers
F1 context presence only. A persistent mismatch is a candidate requiring controls
and repetition. A failed ping, timeout, or missing trace is not a confirmed attack.

Keep complete run folders locally. [Results](validation.md) links the small
tracked evidence sets; [instrumentation](instrumentation.md)
lists configuration and sampling bounds.

Repeat the matched context checks:

```text
python tools/validate_contexts.py --repeats 3
```
