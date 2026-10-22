# Project description

TRUSST-O-RAN investigates security properties at the boundaries between UE,
RU, DU, CU, and RIC components. Disaggregation introduces asynchronous
transactions, distributed resource ownership, and feedback aggregation that
must be evaluated with explicit timing and state observations.

The current task specifications name three invariants:

1. **State consistency:** compatible state across the distributed lifecycle.
2. **Synchronous control transitions:** transitions complete within justified
   procedure windows and measured clock uncertainty.
3. **Feedback consistency:** RIC observations accurately represent relevant
   radio and scheduling behavior.

Experiments should record capability assumptions, software versions, valid
procedure preconditions, achieved timing, source identities, recovery, and
control-detection outcomes. Benign connectivity, software tests, dry-run plans,
and confirmed attack outcomes are distinct evidence classes.

The four available repository specifications define Thrust 1. They refer to
later monitoring and mitigation research; additional task definitions for
those thrusts are not present in the current organization catalog.

## Current status

- A benign virtual CU/DU baseline passed attachment and tunnel traffic on
  2026-10-22. See [validation](validation.md) for scope and cleanup limitations.
- Task 1 has a draft model, candidate S1-S6 plans, and offline analysis tools.
  Initial live UE RLF and single-UE restart mechanisms now collect real runtime
  observations. RLF traffic recovered; the restart observation reached a
  session timeout. Neither establishes a CU/DU inconsistency.
- Tasks 2-4 have research objectives and deliverable checklists. The shared
  baseline alone does not implement their attack mechanisms.

## Authorized laboratory scope

Run experiments on the provided local virtual lab or on systems you own or
are authorized to evaluate. Coordinate responsible disclosure for confirmed
implementation vulnerabilities. No attack success, severity, or protection
bypass is established by the baseline connectivity run.
