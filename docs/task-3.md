# TRUSST-O-RAN Thrust 1, Task 1.3

## E2 Feedback-Loop Poisoning

This repository tracks the modeling, implementation, validation, and dissemination artifacts for Task 1.3 of the TRUSST-O-RAN research plan. The task investigates semantic signal injection by adversarial UEs that indirectly biases near-real-time RIC observations and xApp decisions through manipulated CQI, Buffer Status Report, and HARQ behavior.

## Research Objective

Develop and evaluate a protocol-compliant attack class in which semantically misleading uplink control information affects metrics aggregated over E2 reporting windows. The work will characterize the attack's ability to induce resource-allocation bias, false congestion, slice reallocation, and slice-utility misclassification while remaining syntactically valid at the radio interface.

The task targets:

- Invariant 3: Feedback Consistency for RIC Observations

## Required Deliverables

- [ ] A formal attack model defining the threat assumptions, E2 and KPM observation path, reporting windows, metric provenance assumptions, attack parameters, expected violations, and success conditions.
- [ ] A configurable semantic signal-injection implementation covering CQI, Buffer Status Report, and HARQ behavior.
- [ ] Support for controlled variation of attack-source count, legitimate-UE count, reporting interval, signal strategy, traffic load, and attack duration.
- [ ] Evaluation across multiple O-RAN implementations and project testbeds.
- [ ] A trace corpus containing successful, unsuccessful, and benign executions with synchronized UE, DU, E2/KPM, near-real-time RIC, and xApp observations where available.
- [ ] An implementation-complexity analysis covering signaling requirements, timing requirements, equipment, software dependencies, and repeatability.
- [ ] A severity and breadth analysis documenting effects on co-scheduled UEs, slices, RIC observations, and xApp actions.
- [ ] A comparison of implementation complexity and operational effects with the other Thrust 1 attack classes.
- [ ] Reproducible experiment automation, testbed configuration, data-processing utilities, and execution documentation.
- [ ] A results package containing raw data, processed data, metadata, plots, tables, and a concise interpretation of findings.

## Evaluation and Completion Criteria

- [ ] Enumerate the protocol-compliant attack scenarios generated.
- [ ] Report coverage of relevant UE control behaviors, E2 reporting conditions, RIC observations, xApp decisions, control states, and timing windows.
- [ ] Measure attack success rate and time required to establish a measurable feedback-loop effect.
- [ ] Measure resource-allocation bias, effects on co-scheduled UEs, slice reallocation, false congestion, and slice-utility misclassification.
- [ ] Quantify the influence of attack-source count, legitimate-UE count, reporting interval, traffic conditions, and attack duration.
- [ ] Determine which executions are detected by existing cryptographic, conformance, KPM-validation, and operational controls.
- [ ] Compare severity, breadth, timing precision, and signaling complexity with the other Thrust 1 attacks.
- [ ] Demonstrate that documented experiments can be repeated from a clean environment with the published configuration.

## Reproducibility Package

The completed repository is expected to provide:

- Source code and build instructions.
- Machine-readable experiment and testbed configurations.
- Automation for setup, execution, collection, and analysis.
- Versioned dependency and equipment information.
- Raw UE, DU, E2/KPM, RIC, and xApp traces, or documented retrieval locations when files exceed repository limits.
- Processed datasets with schemas and metadata.
- Expected outputs and validation checks for representative experiments.
- A user guide covering setup, execution, troubleshooting, and result interpretation.

## Dependencies and Integration

The implementation is expected to integrate with the TRUSST-O-RAN Soft T-UE workflow, a near-real-time RIC, relevant xApps, and the project evaluation environments. Testbed-specific components, credentials, commercial software, and external RAN implementations are not assumed to be distributed from this repository.

Outputs from this task are intended to support the monitoring and mitigation research in later TRUSST-O-RAN thrusts.

## Responsible Use

This repository is intended exclusively for authorized security research, controlled laboratory evaluation, education, and defensive validation. Run experiments only on equipment and networks you own or are explicitly authorized to test. Coordinate responsible disclosure before publishing details that could place operational systems at risk.

## License

Software in this repository is licensed under the GNU General Public License v3.0. See [LICENSE](https://github.com/TRUSST-O-RAN/thrust1-task3-e2-feedback-loop-poisoning/blob/main/LICENSE).

## Shared virtual testbed

The organization-wide core/CU/DU/srsUE baseline and all its automation are in
[testbed/virtual](https://github.com/TRUSST-O-RAN/thrust1-task3-e2-feedback-loop-poisoning/blob/main/testbed/virtual/README.md). Start with:

```text
python -m pip install -r testbed/virtual/requirements.txt
python testbed/virtual/scripts/testbed.py check
```

See the [project documentation](https://trusst-o-ran.github.io/) for all tasks,
setup, validation evidence, and task-specific capability limits. This shared
baseline does not implement this task's attack or its additional interfaces.
