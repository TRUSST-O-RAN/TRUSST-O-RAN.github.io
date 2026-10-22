# TRUSST-O-RAN Thrust 1, Task 1.2

## RU-DU Buffer Desynchronization

This repository tracks the modeling, implementation, validation, and dissemination artifacts for Task 1.2 of the TRUSST-O-RAN research plan. The task investigates PHY-aware disruption of the RU-DU feedback loop in an O-RAN 7.2x split, with emphasis on HARQ timing, eCPRI jitter, buffer behavior, and DU scheduling stability.

## Research Objective

Develop and evaluate a protocol-compliant attack class in which an adversarial UE uses fine-grained timing, power, and uplink-control behavior to create HARQ feedback uncertainty and temporal drift between the RU and DU. The work will quantify resulting instability in retransmission scheduling, buffer management, uplink resource allocation, throughput, latency, and fairness.

The task targets:

- Invariant 2: Synchronous Control Transitions

## Required Deliverables

- [ ] A formal PHY-aware attack model defining the threat assumptions, RU-DU timing relationships, HARQ states, buffers, attack parameters, expected violations, and success conditions.
- [ ] A configurable adversarial UE implementation capable of producing timing-sensitive uplink transmissions and high-frequency scheduling-request behavior.
- [ ] Support for controlled variation of transmission timing, power, scheduling-request frequency, payload consistency, HARQ behavior, and attack duration.
- [ ] Evaluation across multiple attack-parameter settings and RAN implementations.
- [ ] Experiments with one and multiple active legitimate UEs during attack execution.
- [ ] A trace corpus containing successful, unsuccessful, and benign executions with synchronized PHY, RU, DU, scheduler, and UE observations where available.
- [ ] An implementation-complexity analysis covering signaling precision, timing precision, equipment, software dependencies, and repeatability.
- [ ] A severity analysis documenting performance degradation, instability, persistence, recovery, and impact on legitimate UEs.
- [ ] Recommendations for RAN original equipment manufacturers and network operators based on observed failure modes.
- [ ] Reproducible experiment automation, testbed configuration, data-processing utilities, and execution documentation.
- [ ] A results package containing raw data, processed data, metadata, plots, tables, and a concise interpretation of findings.

## Evaluation and Completion Criteria

- [ ] Enumerate the protocol-compliant attack scenarios generated.
- [ ] Report coverage of relevant PHY, HARQ, scheduling, buffer, control-state, and timer transitions.
- [ ] Measure attack success rate and time required to establish RU-DU or HARQ desynchronization.
- [ ] Measure throughput, latency, fairness, retransmission behavior, buffer stability, and uplink-allocation effects.
- [ ] Quantify the influence of timing, power, request frequency, attack duration, and legitimate-UE contention.
- [ ] Determine which executions are visible to existing cryptographic, RRC/NAS conformance, logging, and operational controls.
- [ ] Compare results across tested RAN implementations using consistent scenarios and metrics.
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

## Dependencies and Integration

The implementation is expected to integrate with the TRUSST-O-RAN Soft T-UE workflow and the project evaluation environments. Testbed-specific components, credentials, commercial software, and external RAN implementations are not assumed to be distributed from this repository.

Outputs from this task are intended to support the monitoring and mitigation research in later TRUSST-O-RAN thrusts.

## Responsible Use

This repository is intended exclusively for authorized security research, controlled laboratory evaluation, education, and defensive validation. Run experiments only on equipment and networks you own or are explicitly authorized to test. Coordinate responsible disclosure before publishing details that could place operational systems at risk.

## License

Software in this repository is licensed under the GNU General Public License v3.0. See [LICENSE](https://github.com/TRUSST-O-RAN/thrust1-task2-ru-du-buffer-desynchronization/blob/main/LICENSE).

## Shared virtual testbed

The organization-wide core/CU/DU/srsUE baseline and all its automation are in
[testbed/virtual](https://github.com/TRUSST-O-RAN/thrust1-task2-ru-du-buffer-desynchronization/blob/main/testbed/virtual/README.md). Start with:

```text
python -m pip install -r testbed/virtual/requirements.txt
python testbed/virtual/scripts/testbed.py check
```

See the [project documentation](https://trusst-o-ran.github.io/) for all tasks,
setup, validation evidence, and task-specific capability limits. This shared
baseline does not implement this task's attack or its additional interfaces.
