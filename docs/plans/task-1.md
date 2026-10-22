---
orphan: true
---

# Task 1.1 research plan

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
