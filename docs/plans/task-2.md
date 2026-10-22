---
orphan: true
---

# Task 1.2 research plan

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
