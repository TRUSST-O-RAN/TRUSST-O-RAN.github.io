# Task 1 scenario implementation

The candidate S1-S6 plans describe hypotheses, not measured vulnerabilities.
The implementation distinguishes UE-originated behavior from mechanisms that
need control of F1 transport or CU/DU endpoint hooks.

| Scenario | Candidate mechanism | Implementation prerequisite |
| --- | --- | --- |
| S1 | Overlapping context setup | Valid endpoint scheduling and F1 procedure hooks |
| S2 | Modification/release race | Procedure hooks and correlated resource cleanup |
| S3 | Radio-link failure cleanup | Controlled UE RLF trigger and recovery observations |
| S4 | Reset during context procedure | Endpoint-controlled Reset and valid scope |
| S5 | Security/bearer overlap | CU/UE security instrumentation and bearer events |
| S6 | Concurrent lifecycle overlap | Independently provisioned UEs and real radio multiplexing |

The initial live implementation will add bounded UE RLF and reconnect
experiments on the shared lab. A single-UE restart is an initial lifecycle
experiment, not a concurrent attach flood or a clean NAS detach. Stock logs
and successful commands do not establish internal CU/DU state consistency.
