---
orphan: true
---

# Task 1.4 research plan

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
