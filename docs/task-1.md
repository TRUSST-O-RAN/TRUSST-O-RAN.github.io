# TRUSST-O-RAN Thrust 1, Task 1.1

## Cross-Split State Desynchronization

This repository tracks the modeling, implementation, validation, and dissemination artifacts for Task 1.1 of the TRUSST-O-RAN research plan. The task investigates timing-induced state divergence across the O-RAN CU-DU split, with emphasis on F1-C procedures associated with UE attachment, radio bearer setup, and security state transitions.

## Research Objective

Develop and evaluate a protocol-compliant attack class in which adversarial UE signaling and precisely controlled timing cause CU and DU state machines to commit inconsistent bearer or security states. The work will characterize how deployment disaggregation, asynchronous F1AP transactions, timer skew, and scheduling jitter affect the feasibility and impact of the attack.

The task targets:

- Invariant 1: State Consistency
- Invariant 2: Synchronous Control Transitions

## Required Deliverables

- [ ] A formal attack model defining the threat assumptions, affected interfaces, relevant protocol states, event sequences, timers, attack parameters, expected state violations, and success conditions.
- [ ] A configurable Soft T-UE attack implementation for adversarial attach-detach and overlapping control-message sequences.
- [ ] Support for controlled variation of attack-source count, subscriber-identity behavior, timing offset, timing precision, and jitter.
- [ ] White-box O-RAN validation with access to internal CU and DU state.
- [ ] Black-box O-RAN validation using externally observable outcomes.
- [ ] A benchmark comparison with at least one traditional, non-disaggregated 5G RAN implementation.
- [ ] A trace corpus containing successful, unsuccessful, and benign executions with synchronized UE, CU, DU, and network observations where available.
- [ ] An implementation-complexity analysis covering signaling requirements, timing requirements, equipment, software dependencies, and repeatability.
- [ ] A severity analysis documenting the breadth, duration, recoverability, and operational impact of each demonstrated state inconsistency.
- [ ] Reproducible experiment automation, testbed configuration, data-processing utilities, and execution documentation.
- [ ] A results package containing raw data, processed data, metadata, plots, tables, and a concise interpretation of findings.

## Evaluation and Completion Criteria

- [ ] Enumerate the protocol-compliant attack scenarios generated.
- [ ] Report coverage of relevant attachment, bearer, security, F1AP, control-state, and timer transitions.
- [ ] Measure attack success rate and time required to establish a successful state inconsistency.
- [ ] Measure the effect of timing precision, jitter, and single versus multiple attack sources.
- [ ] Record stale MAC contexts, duplicated or unmanaged data radio bearers, failed attachment, service degradation, and recovery behavior.
- [ ] Determine which executions are detected by existing cryptographic, conformance, or operational controls.
- [ ] Compare white-box, black-box, disaggregated, and monolithic RAN results using consistent scenarios and metrics.
- [ ] Demonstrate that documented experiments can be repeated from a clean environment with the published configuration.

## Reproducibility Package

The completed repository is expected to provide:

- Source code and build instructions.
- Machine-readable experiment and testbed configurations.
- Automation for setup, execution, collection, and analysis.
- Versioned dependency and equipment information.
- Raw traces and measurements, or documented retrieval locations when files exceed repository limits.
- Processed datasets with schemas and metadata.
- Expected outputs and validation checks for representative experiments.
- A user guide covering setup, execution, troubleshooting, and result interpretation.

## Offline Trace Consistency Check

`tools/trace_consistency.py` compares exported CU and DU state observations from a JSONL trace. It performs no network I/O. Each record must contain `timestamp_ns` (integer), `component` (`CU` or `DU`), `ue_id`, `transaction_id`, `state_key`, and `state_value`. For each UE, transaction, and state key, the checker compares the latest observed CU and DU values. Unpaired observations are reported separately and are not treated as mismatches.

Run it with:

```text
python tools/trace_consistency.py path\to\trace.jsonl
```

The command exits with status 1 when mismatches are found, 0 when none are found, and 2 for invalid input or file errors. This basic checker does not infer protocol semantics or establish causality; it is intended for offline triage of already-collected traces.

## Dependencies and Integration

Organization documentation: [TRUSST-O-RAN](https://trusst-o-ran.github.io/).
The self-contained lab is shared across all task repositories under `testbed/virtual`.

The implementation is expected to integrate with the TRUSST-O-RAN Soft T-UE workflow and the project evaluation environments. Testbed-specific components, credentials, commercial software, and external RAN implementations are not assumed to be distributed from this repository.

Outputs from this task are intended to support the monitoring and mitigation research in later TRUSST-O-RAN thrusts.

## Implementation Progress (2026-10-22)

The research deliverables above remain open until validated experiment evidence
exists. The repository currently provides these implementation milestones:

- [x] [Draft threat/state model and S1-S6 hypotheses](https://github.com/TRUSST-O-RAN/thrust1-task1-cross-split-desynchronization/blob/main/docs/attack_model.md), with separate UE-only and transport-controlled capabilities.
- [x] [Virtual testbed configuration](https://github.com/TRUSST-O-RAN/thrust1-task1-cross-split-desynchronization/blob/main/testbed/virtual/README.md) based on the OCUDU CU/DU and srsUE documentation: complete Open5GS core, `ocu`, `odu`, and a matching srsUE virtual radio.
- [x] Pinned source preparation, cross-component configuration checks, benign attach/data smoke automation, and run-evidence collection in `testbed/virtual/scripts/testbed.py`.
- [x] Offline state consistency checks and regression coverage for testbed wiring and evidence classification.
- [x] Build the container images and record a successful benign smoke run on Docker Desktop's WSL2 Linux backend. The [2026-10-22 run](https://github.com/TRUSST-O-RAN/thrust1-task1-cross-split-desynchronization/blob/main/results/benign-baseline-20261022-02/metadata.json) established N2/F1 connectivity, a UE PDU session, and 3/3 tunnel pings with 0% packet loss.
- [x] Start [live Task 1 lifecycle experiments](https://github.com/TRUSST-O-RAN/thrust1-task1-cross-split-desynchronization/blob/main/docs/live_scenarios.md): a verified UE RLF console trigger and a bounded single-UE restart backend with real traffic/evidence collection. The RLF run recovered traffic; the restart run timed out awaiting a fresh session. Neither establishes an inconsistency.
- [ ] Integrate a verified Soft T-UE backend and valid F1AP transport/encoding. Legacy F1-injection plans remain unavailable for live execution; the limited `--backend virtual` supports only the new lifecycle plans.
- [ ] Instrument internal CU/DU state and correlate UE lifecycle/procedure identifiers. Stock OCUDU logs and PCAPs do not automatically export the checker's state schema.
- [ ] Measure the attack scenarios, coverage, timing/source sweeps, control detection, severity, recovery, and monolithic comparison; assemble the measured corpus and results.

Run offline validation from the repository root:

```text
python -m pip install -r requirements.txt
python -m pytest -q
python testbed/virtual/scripts/testbed.py check
python tools/scenario_runner.py scenarios/s1_overlapping_context_setup.yaml --dry-run
```

The scenario dry run produces a plan with `evidence_kind: dry_run` and
`success: false`; a zero process exit code means planning completed. It does
not contact the RAN. The Soft T-UE wrapper still has offline fallback behavior,
and the F1AP probe is an encoding prototype whose conformance is unverified.

For the virtual testbed, follow [setup and smoke-test instructions](https://github.com/TRUSST-O-RAN/thrust1-task1-cross-split-desynchronization/blob/main/testbed/virtual/README.md).
For the initial live S3/S6 variants, follow [live scenario instructions](https://github.com/TRUSST-O-RAN/thrust1-task1-cross-split-desynchronization/blob/main/docs/live_scenarios.md).
See [evaluation gates and analysis limits](https://github.com/TRUSST-O-RAN/thrust1-task1-cross-split-desynchronization/blob/main/docs/evaluation.md) for the evidence
needed to complete the remaining research deliverables. Existing metrics and
corpus-label heuristics require validation before use in reported results.

## Responsible Use

This repository is intended exclusively for authorized security research, controlled laboratory evaluation, education, and defensive validation. Run experiments only on equipment and networks you own or are explicitly authorized to test. Coordinate responsible disclosure before publishing details that could place operational systems at risk.

## License

Software in this repository is licensed under the GNU General Public License v3.0. See [LICENSE](https://github.com/TRUSST-O-RAN/thrust1-task1-cross-split-desynchronization/blob/main/LICENSE).
