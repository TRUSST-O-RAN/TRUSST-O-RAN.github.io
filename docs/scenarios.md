# Initial live Task 1 scenario backend

The `virtual` backend in `tools/scenario_runner.py` runs bounded lifecycle
experiments using the shared local lab. These are initial mechanisms for S3
and S6, separate from the unvalidated legacy F1-injection plans.

Prepare/build the lab using [testbed/virtual](virtual-setup.md), then:

```text
python tools/scenario_runner.py scenarios/live/s3_ue_radio_link_failure.yaml --backend virtual --trace-dir traces/live-task1
python tools/scenario_runner.py scenarios/live/s6_single_ue_reconnect.yaml --backend virtual --trace-dir traces/live-task1
```

`--dry-run` produces a plan including `virtual_plan` and does not start Docker.
A live process exit code of zero means the observation run completed. It does
not mean an attack succeeded. Unsupported capabilities/configuration return 2;
runtime infrastructure failures return 1 and retain evidence when startup was
attempted.

## Implemented behavior

- Establish a fresh core/CU/DU/UE stack, require N2/F1/PDU readiness, and verify
  tunnel traffic before applying a perturbation.
- **S3 initial variant:** deliver the stock UE's `rlf` console command through
  Docker's local attach API and require a fresh UE acknowledgement. This is
  internal RLF simulation, not proof of an over-the-air T310 expiry.
- **S6 initial variant:** restart the one provisioned UE, require a new PDU
  session, and probe tunnel traffic. This is abrupt UE loss/reconnect, not clean
  NAS deregistration, concurrent sources, or an attach flood.
- Execute 1-5 cycles, stopping after failed recovery; accept one fixed identity
  only. Use a recorded random seed and clipped Gaussian inter-action jitter.
  Offset/jitter are limited to 0-1 second; per-phase readiness/recovery
  timeouts are 5-180 seconds. Docker startup/shutdown has separate deadlines.
- Retain baseline and per-attempt ping results, pre-restart UE log snapshots,
  fresh console slices, host monotonic/wall timestamps, the scenario, backend
  source, application logs, PCAPs, image identifiers, and configuration hashes.

Host waits and action durations are measured. They are not achieved radio or
F1 delivery precision. The Docker context must use a local Unix socket or
Windows named pipe for the RLF console control.

## Observations and classification

On 2026-10-22 the live S3 variant attached, acknowledged `Sending Radio Link
Failure`, reported `Detected Radio-Link Failure`, and subsequently received
all three tunnel-ping replies. Two S6 restart observations did not regain
a PDU session within 45 seconds and stopped after one of two planned cycles.
The final run also recorded a failed traffic probe because `tun_srsue` was
absent. The cause has not been established; virtual-radio clock/restart behavior and
RAN cleanup need separate diagnosis.

Those original lifecycle observations are labelled `inconclusive`, with `success: false`
and `white_box_available: false`. A missing trigger acknowledgement is instead
an `infrastructure_failure`. Event JSONL records describe actions and console
observations; they are deliberately not the CU/DU state checker's schema.
No successful command, packet reply, timeout, or stock log is synthesized into
a normalized internal state fact.

## Remaining implementation

An optional [native instrumentation overlay](instrumentation-overview.md) now provides
bounded DU setup/modification/release delay hooks and actual F1 context state.
Instrumented plans record native coverage separately; the generic event JSONL
continues to contain only controller/console observations.

S1/S2 need verified overlap scheduling and actual bearer/resource tables beyond
the new serial procedure delay hooks. S4 needs reset hooks and scope validation.
S5 needs CU/UE security and bearer instrumentation. Full S6
needs independently provisioned UEs and a verified virtual-radio multiplexer.
Broader white-box exports, association correlation, clock bounds, settling
windows, repeated controls, and recovery analysis remain necessary before classifying
an inconsistency or reporting attack success rates.
