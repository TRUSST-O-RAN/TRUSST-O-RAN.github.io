# Attack model

Task 1 asks whether CU and DU state remains incompatible after a control procedure
finishes. The current lab uses Open5GS, a split OCUDU CU/DU, and one srsUE.

## Capabilities

- **UE-only:** attach, reconnect, and supported UE signaling controls.
- **Endpoint-controlled:** installed CU/DU hooks delay native F1 procedures.

Record which capability a test uses. An endpoint delay is not a demonstrated
UE-only attack. The old F1 byte-construction plans are unvalidated and refuse live execution.

## State to compare

CU and DU own different layers: CU has RRC/PDCP; DU has RLC/MAC/PHY. They need
compatible context and bearer ownership, not identical private state. Security
activation belongs to CU/UE observation, not comparison of DU ciphering keys.

Native F1 IDs, process epochs, and allocation epochs identify each UE lifetime.
An offline procedure ordinal is a correlation label, not a wire Transaction ID.

## Scenarios

| ID | Question | Still needed |
|---|---|---|
| S1 | Can overlapping setup leave incompatible allocations? | Verified overlap and bearer tables |
| S2 | Can modification/release races leave resources behind? | Resource exports and overlap scheduling |
| S3 | Does RLF cleanup leave one side allocated? | Repeated state and recovery checks |
| S4 | Does reset interrupt cleanup? | Native reset hooks and scope checks |
| S5 | Can security and bearer transitions diverge? | CU/UE security observations |
| S6 | Can concurrent reconnects orphan contexts? | Multiple provisioned UEs and virtual-radio support |

## A finding must show

1. A valid procedure and an unambiguous UE lifetime.
2. A state difference after pending work and a justified cleanup interval.
3. Complete observations on comparable clocks.
4. Repetition against a matched control, with service impact and recovery recorded.

The implemented checker samples **F1 context presence**. It excludes pending
procedures, checks native clock offsets, and reports persistent differences as
candidates. It cannot establish bearer, scheduler, or security consistency.
No confirmed attack is currently recorded.

[Experiments](experiments.md) · [Research requirements](plans/task-1.md)
