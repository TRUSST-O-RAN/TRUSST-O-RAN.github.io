# Cross-split state desynchronization model

Version 1.1, 2026-10-22. Research draft; candidate scenarios have not been
demonstrated against a running RAN. The model distinguishes UE-originated
behavior from experiments that require control of the lab's F1 transport.

## System and trust boundaries

The reference system contains an Open5GS core, an OCUDU CU (CU-CP and CU-UP),
an OCUDU DU, and srsUE. CU and DU communicate using F1-C/SCTP and F1-U/GTP-U;
the DU and UE exchange virtual RF samples using ZeroMQ. See the
[OCUDU split guide](https://docs.ocudu.org/tutorials/cu_du_split/).

The CU terminates RRC and PDCP; the DU holds RLC, MAC, and PHY state. See
[OCUDU components](https://docs.ocudu.org/knowledge_base/gnb_components/).
CU/DU consistency therefore means compatible distributed state, not identical
copies of every key. In particular, AS ciphering keys at the UE/CU are not
shared DU ciphering state. Security experiments must observe CU/UE activation
and its relationship to bearer lifecycle, or extend the observation model.

Two experimental capabilities must be recorded separately:

1. **UE-only:** a provisioned laboratory UE controls its own attach, detach,
   reconnection, identities from a provisioned pool, and supported signaling
   timings. It cannot fabricate F1AP PDUs or arbitrarily delay protected RRC
   messages merely by being a UE.
2. **Transport-controlled:** an explicitly installed lab proxy, instrumented
   CU/DU, or endpoint hook schedules F1 procedure delivery. This requires
   access beyond the UE threat model. Reaching SCTP port 38472 does not grant
   access to another association, its streams, or valid UE contexts.

The configured lab does not enable transport security. Its absence is a local
configuration fact, not a claim that every deployment permits injection.
Authentication, association checks, transport protection, and RRC integrity
must be recorded as controls and measured independently. A Reset procedure
is not equivalent to selectively terminating an SCTP stream.

## State, events, and correlation

For UE lifecycle epoch `u`, procedure instance `p`, bearer `b`, and component
`x`, let `s_x(u,p,b,t)` be a normalized observation. Candidate shared facts
include context existence, bearer identity, allocation/release completion,
and the active transport binding. Component-private facts such as MAC
allocation require a stated mapping to the corresponding CU lifecycle state.

The baseline lifecycle is:

```text
absent -> setup_pending -> active -> modification_pending -> active
active -> release_pending -> absent
pending/active -> reset_or_failure_cleanup -> absent
```

Each event must identify component, UE epoch, direction, procedure, local UE
identifiers, monotonic and wall-clock timestamps, and observation provenance.
Correlation must map CU and DU F1AP UE identifiers to one lifecycle. A local
`transaction_id` in our trace schema is an experiment correlation token; it
does not imply that every F1AP UE-associated PDU carries a Transaction ID IE.

## Invariants and success

Define a per-key compatibility relation `C_k`, a measured clock uncertainty
`epsilon`, and a justified settling window `W_p` for each procedure.

- **State consistency:** after procedure completion and its cleanup window,
  `C_k(s_CU(u,p,b,t), s_DU(u,p,b,t))` holds for each mapped distributed fact.
  Identical normalized keys use equality. Pending procedures may legitimately
  have different local states.
- **Bounded transition skew:** correlated transitions obey
  `abs(t_CU - t_DU) <= W_p + epsilon`. Direction and ordering depend on the
  procedure; a global assumption that CU always transitions first is invalid.

A confirmed inconsistency requires paired, correlated observations after the
settling window, reproducibility against a benign control, and evidence that
the mismatch is not missing capture or stale identity reuse. A timing violation
must exceed clock uncertainty and the relevant procedure bound. The initial
10 ms analysis threshold is an experimental parameter, not a protocol limit.

The current checker compares the latest values per `(ue_id, transaction_id,
state_key)` and reports unmatched groups separately. It is a triage tool: it
does not determine procedure completion, compatibility mappings, duration,
recovery, or causality. Its `--causal` heuristic must not be treated as a
universal F1AP conformance rule. Empty or unpaired traces cannot establish
attack failure or benign consistency.

## Candidate scenarios

The YAML files enumerate hypotheses and timing plans. Their messages and
mandatory IEs still need validation against the pinned F1AP ASN.1 schema and
the actual endpoint state before any protocol-compliance claim.

| ID | Hypothesis | Capability required | Evidence needed |
|---|---|---|---|
| S1 | Overlapping setup creates inconsistent bearer allocation | Transport-controlled unless mapped to valid UE-triggered procedures | Correlated setup outcomes and bearer tables |
| S2 | Modification and release race leaves stale resources | Transport-controlled timing or demonstrated UE-triggered overlap | CU lifecycle plus DU RLC/MAC cleanup |
| S3 | RLF handling leaves one side's context allocated | UE-triggered link loss; spoofed F1 variant is transport-controlled | RLF indication, release exchange, cleanup/recovery |
| S4 | Reset overlaps an in-flight context procedure | Transport-controlled | Valid Reset scope, procedure outcome, post-reset allocation |
| S5 | Security activation overlaps bearer transition | Requires revised CU/UE observation model | RRC/PDCP activation and bearer events; not DU ciphering keys |
| S6 | Concurrent attach/reconnect increases orphan lifecycles | UE-only with independently provisioned sources | Per-source registration, context correlation, resource recovery |

F1AP byte construction in `tools/f1ap_probe.py` is a prototype and is not
validated ASN.1 aligned-PER encoding. Installing `pyasn1` does not supply an
F1AP schema or prove conformance. The scenario runner refuses live execution
until a real transport and state collector are integrated. Dry runs are plans.

## Timers and controlled parameters

Record source count, subscriber identity policy, requested offset, achieved
offset, jitter distribution, random seed, repetitions, baseline load, and CPU
placement. Report measured timing error; nanosecond input units do not imply
nanosecond delivery precision. The current runner plans offset sweeps; source
count, jitter, and identity policies are not yet wired into live execution.

Reference configuration uses `cu_cp.inactivity_timer` in seconds. RRC T310 and
T311 belong to UE timer behavior configured through broadcast system information,
not invented DU top-level `timers` settings. SCTP retransmission, F1 procedure
deadlines, scheduling, and RRC timers must be measured and varied separately.
Preserve effective configuration and implementation versions for every run.

## Outcomes and impact

Distinguish `confirmed_inconsistency`, `completed_no_inconsistency`,
`inconclusive`, `infrastructure_failure`, and `dry_run`. Only complete, measured
attack runs belong in a success-rate denominator. Record first observable
violation, observation duration, recovery trigger, service interruption, affected
UE/bearer count, packet loss, attach latency, and detection/control outcomes.
An unobserved metric is null/unknown, not zero.

No severity, attack success rate, or cryptographic bypass has been established.
White-box instrumentation, black-box baselines, and a separate non-disaggregated
5G RAN comparison remain required. See [evaluation.md](https://github.com/TRUSST-O-RAN/thrust1-task1-cross-split-desynchronization/blob/main/docs/evaluation.md) for the
evidence gates and [the repository policy](https://github.com/TRUSST-O-RAN/thrust1-task1-cross-split-desynchronization/blob/main/README.md#responsible-use) for
authorized laboratory scope.
