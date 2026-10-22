# TRUSST-O-RAN Thrust 1, Task 1.4

## Adversarial Random-Access Perturbations

This repository tracks the modeling, implementation, validation, and dissemination artifacts for Task 1.4 of the TRUSST-O-RAN research plan. The task investigates adversarial perturbation of the 5G random-access and session-establishment procedure, including incomplete MSG1-MSG5 sequences and contention behavior that consumes RAN control resources or disrupts legitimate UE attachment.

## Research Objective

Develop and evaluate protocol-compliant denial-of-service scenarios in which malicious UEs intentionally leave random-access or RRC setup procedures incomplete or interfere with contention-related transmissions. The work will determine how asynchronous timers, message reordering, control-plane disaggregation, and containerized deployments affect the attack's feasibility and impact relative to monolithic 5G RANs.

The task targets:

- Invariant 2: Synchronous Control Transitions

## Required Deliverables

- [ ] A formal attack model defining the threat assumptions, MSG1-MSG5 state sequence, RRC contexts, relevant timers, attack variants, expected violations, and success conditions.
- [ ] A configurable implementation covering incomplete setup after MSG4, missing MSG5 responses, MSG3 contention behavior, and other validated sequence variants.
- [ ] Support for controlled variation of attacker count, request rate, timing, sequence selection, attack duration, identity behavior, and offered load.
- [ ] Experimental validation across multiple parameter settings, RAN contexts, and RAN implementations.
- [ ] A controlled comparison of disaggregated O-RAN and traditional monolithic 5G RAN behavior.
- [ ] A trace corpus containing successful, unsuccessful, and benign executions with synchronized UE, RAN, random-access, RRC, timer, and resource observations where available.
- [ ] An implementation-complexity analysis covering signaling requirements, timing requirements, equipment, software dependencies, and repeatability.
- [ ] A severity analysis documenting resource exhaustion, legitimate-UE disruption, persistence, recovery, and operational impact.
- [ ] A comparison of complexity and severity with the other Thrust 1 attack classes.
- [ ] Reproducible experiment automation, testbed configuration, data-processing utilities, and execution documentation.
- [ ] A results package containing raw data, processed data, metadata, plots, tables, and a concise interpretation of findings.

## Evaluation and Completion Criteria

- [ ] Enumerate the protocol-compliant attack scenarios generated.
- [ ] Report coverage of relevant random-access, RRC, control-state, and timer transitions.
- [ ] Measure attack success rate and time required to establish resource exhaustion or measurable attachment disruption.
- [ ] Measure legitimate-UE attachment success, setup latency, allocated contexts, resource consumption, service degradation, and recovery behavior.
- [ ] Quantify the influence of attacker count, request rate, timing, sequence variant, attack duration, and deployment architecture.
- [ ] Determine which executions are detected by existing cryptographic, conformance, rate-control, and operational controls.
- [ ] Compare disaggregated and monolithic RAN results using consistent scenarios and metrics.
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

Software in this repository is licensed under the GNU General Public License v3.0. See [LICENSE](https://github.com/TRUSST-O-RAN/thrust1-task4-random-access-perturbations/blob/main/LICENSE).

## Shared virtual testbed

The organization-wide core/CU/DU/srsUE baseline and all its automation are in
[testbed/virtual](https://github.com/TRUSST-O-RAN/thrust1-task4-random-access-perturbations/blob/main/testbed/virtual/README.md). Start with:

```text
python -m pip install -r testbed/virtual/requirements.txt
python testbed/virtual/scripts/testbed.py check
```

See the [project documentation](https://trusst-o-ran.github.io/) for all tasks,
setup, validation evidence, and task-specific capability limits. This shared
baseline does not implement this task's attack or its additional interfaces.
