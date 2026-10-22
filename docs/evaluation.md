# Evaluation and completion gates

Updated 2026-10-22. No empirical attack results have been collected in this
checkout. Unit tests, configuration checks, dry runs, and synthetic fixtures
are software validation only.

| Gate | Available now | Remaining evidence |
|---|---|---|
| Model | Revised threat/state model and S1-S6 hypotheses | ASN.1/procedure review and valid state mappings |
| Virtual baseline | Pinned builds and a [successful WSL2 benign attach and tunnel-ping run](https://github.com/TRUSST-O-RAN/thrust1-task1-cross-split-desynchronization/blob/main/results/README.md) | Repeat from a clean environment; archive images for binary replay |
| Soft T-UE | Wrapper and offline stubs | Verified external binary API, real RF/signaling integration and acknowledgements |
| Timing campaign | YAML plans and dry-run offset sweeps | Achieved delivery timing, source/identity/jitter implementation and repetitions |
| White-box | Trace schema, consistency checker, custom-log adapter | Instrumented CU/DU exports, UE epoch mapping, procedure completion and clock bounds |
| Black-box | One successful benign attach with 3/3 tunnel pings | Repeated attach latency, loss, throughput, recovery, and control-detection baselines |
| Comparison | Common proposed metrics | Separate traditional non-disaggregated 5G RAN with matched UE/core/workload |
| Corpus/results | Packaging and aggregate utilities | Validated measured labels, raw/processed traces, plots, tables and interpretation |

The main README deliverables remain unchecked until their research evidence
exists. A combined OCUDU `gnb` process could be an additional deployment
baseline, but does not by itself fulfill a comparison against a traditional
non-disaggregated RAN implementation.

## Run procedure

1. Complete the [testbed setup](https://github.com/TRUSST-O-RAN/thrust1-task1-cross-split-desynchronization/blob/main/testbed/virtual/README.md), retain build logs, and run
   a benign smoke test into a new output directory. Archive the images and run
   folder. Resolve all failed capture commands in `metadata.json`.
2. Install state instrumentation with a documented patch and capture UE/CU/DU
   observations on the same host clock, or measure cross-host clock uncertainty.
   Preserve raw timestamps and record the correlation of local UE identifiers.
3. Validate each candidate message against the pinned schema and procedure
   preconditions. Record rejected candidates; do not count rejected malformed
   PDUs as protocol-compliant attack scenarios.
4. Freeze scenario, software, core subscriber pool, workload, and timing matrix.
   Run matched benign and attack conditions with recorded seeds and repetition
   counts. Treat startup/capture failures as infrastructure failures.
5. Export normalized state only from real observations, then run the checker.
   Manually validate representative mismatches against procedure boundaries,
   cleanup windows, and packet captures before labeling success.
6. Measure black-box service effects and recovery separately. Repeat against
   the selected monolithic implementation under comparable load. State which
   observations are unavailable rather than inventing corresponding values.

## Per-run record

Keep the run ID, scenario/version, experiment capability (UE-only or
transport-controlled), source identity pool, seed, requested and achieved
timing distributions, source count, clock uncertainty, configuration/image
hashes, instrumentation version, capture completeness, and outcome class.

For each scenario's coverage row, record attempted and completed procedures,
state transitions, timer events, and valid/invalid/out-of-state message
outcomes. Denominators must identify eligible measured runs, excluding dry
runs and infrastructure failures.

Implementation-complexity records should list signaling prerequisites, endpoint
or proxy modifications, hardware, build/runtime dependencies, measured timing
precision, operator steps, and repeatability. The current virtual baseline
needs no SDR but does require Linux SCTP, TUN, container capabilities, and a
software UE. These are setup requirements, not measured attack complexity.

Severity records should include affected UE/bearer counts, duration and clock
bounds, measured traffic/registration effects, resource growth, recovery action
(automatic/procedure/restart), and repeatability. Claims about cryptographic,
conformance, or operational controls need observed outcomes for each control.

## Analysis limits

`tools/trace_consistency.py` expects one combined JSONL file in the root README
schema. Latest-value comparison can miss a transient mismatch that recovered;
unpaired groups are incomplete evidence. Timer-gap warnings alone do not prove
an implementation defect. Duration and causal-sequence reconstruction still
need implementation and validation.

`tools/metrics_reporter.py` and `tools/corpus_generator.py` are preliminary.
Their mismatch-based success/label heuristics are not validated research labels.
In particular, a trace with no mismatches may have no paired observations or
may be a failed attack; preserve the explicit run outcome and provenance before
aggregating. Synthetic examples and dry-run plans must be stored separately
from measured traces. Do not publish their counts as attack success rates.
