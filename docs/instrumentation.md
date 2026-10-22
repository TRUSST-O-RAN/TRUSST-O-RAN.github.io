# Task 1 native hooks and internal state

This optional overlay instruments the pinned OCUDU build. The portable
19-file shared bundle and clean source checkout remain unchanged. This
extension belongs to Task 1; the other organization task repositories retain
the common connectivity baseline.

Prepare the [portable lab](virtual-setup.md), build its core and UE images, then
run these commands from the repository root with Docker on `PATH`:

```text
python testbed/virtual/task1/instrument.py build
python tools/scenario_runner.py scenarios/live/instrumented_control.yaml --backend virtual --trace-dir traces/live-task1-instrumented
python tools/scenario_runner.py scenarios/live/instrumented_setup_delay.yaml --backend virtual --trace-dir traces/live-task1-instrumented
python tools/scenario_runner.py scenarios/live/instrumented_modification_delay.yaml --backend virtual --trace-dir traces/live-task1-instrumented
python tools/scenario_runner.py scenarios/live/instrumented_release_control.yaml --backend virtual --trace-dir traces/live-task1-instrumented
python tools/scenario_runner.py scenarios/live/instrumented_release_delay.yaml --backend virtual --trace-dir traces/live-task1-instrumented
```

Builds use six parallel compiler jobs, matching the validated 16 GB WSL2
host. The Dockerfile also accepts `BUILD_JOBS` for a manual build; retain
the instrumentation fingerprint build argument computed by `instrument.py`.
The first build can take substantially longer than an incremental build.
`--dry-run` validates a scenario without running Docker.

## Hook locations and configuration

Hooks run inside the DU's existing decoded UE Context Setup, Modification,
and Release procedures. They retain the implementation's native encoding,
UE mapping, and procedure queues. They do not inject arbitrary messages,
force same-UE overlap, reset a peer, or bypass validation.

| Setting under `virtual.instrumentation` | Hook location / behavior |
|---|---|
| `setup_ms` | After context lookup/creation and CU ID binding, before the DU configuration request |
| `modification_ms` | Before the DU configuration update |
| `release_ms` | Before marking the context for release and removing lower-layer resources |
| `inactivity_s` | Optional supported CU inactivity timer, 5–120 seconds; effective CU configuration is archived |

Delays are integer milliseconds from 0 through 2000, applied to every matching
procedure in that run. Zero leaves an instrumented control. The hooks await
OCUDU timers rather than sleeping on the executor. Each entry and resume
exports native monotonic time and the requested delay. Actual waits can
exceed their request under load; inputs are not radio/F1 delivery precision.
Requested nonzero hooks must complete with at least the requested wait minus
2 ms timer tolerance, or the run reports an instrumentation failure. A hook
that was never reached does not count as a validated perturbation.

The release scenario uses `action: ue_idle_release` with an eight-second
inactivity timer. It first verifies tunnel traffic, waits for a correlated
release, and then sends traffic to observe recovery. The control, setup,
and modification checks use `action: observe`, which attaches and probes
traffic without issuing a UE perturbation. Existing RLF/restart scenarios
can opt in by adding `instrumentation: {}` or the desired delay settings.

## Native exports and provenance

`ocudu.patch` applies only after LF-normalized SHA-256 checks of all ten
patched source files. It is applied inside the Docker builder, leaving
`sources/ocudu` clean. The runtime image carries the pinned commit and a
fingerprint covering the patch, source hashes, header, and Dockerfile. The
runner rejects a stale/mismatched image before starting the stack.

The optional header writes `CU-state.jsonl` and `DU-state.jsonl` to the run's
fresh bind mount. Existing files or write failures abort the instrumented
process, preventing silent stale or incomplete evidence. Each flushed record
has schema `trusst.f1-state.v1` and includes:

- Experiment run ID; random process epoch; strictly increasing sequence.
- Native wall and monotonic timestamps, local UE ID and local allocation epoch.
- Actual CU/DU F1AP identifiers, including an explicitly unbound identifier.
- F1 context presence at repository creation/deletion, and the release flag.
- The DU F1 configuration state: `0=no_config`, `1=config_pending`,
  `2=config_applied`; CU uses `-1=unavailable` for this DU-specific field.
- Procedure send/begin/success/failure observations and hook entry/resume.

Snapshots are taken at the patched lifecycle/procedure points, not periodically.
Hook entry/resume carry the entry snapshot; they are timing observations,
not fresh reads of mutable state after the wait. Release completion after
DU context deletion uses saved command identifiers, never the freed context.
Its local ID is `-1` and allocation epoch `0`; repository deletion is the
separate authoritative absence observation.

Every run archives the backend and instrumentation sources, scenario,
`effective-compose.yml`, optional `instrumented-cu.yml`, image ID/labels,
native JSONL, state report, logs/PCAPs, and traffic probes. The raw effective
Compose file is authoritative for the overlay; top-level `compose_config.txt`
and `docker-compose.yml` describe the portable baseline. `metadata.json`
hashes the captured raw evidence. Complete archives remain local under
`traces/live-task1-instrumented/` because logs and captures are large.

## Correlation and limits

To re-analyze an archive, use its recorded run ID:

```text
python testbed/virtual/task1/instrument.py report traces/live-task1-instrumented/virtual-RUN-ID/raw --run-id RUN-ID
```

The analyzer rejects foreign runs, missing or changed process epochs,
sequence gaps, invalid snapshots, and observations outside a recorded
allocation lifecycle. Reused CU/DU identifier pairs are ambiguous and are
not joined across allocation epochs. A procedure is correlated only when
native CU send, DU begin, DU successful response, and CU successful result
form a complete, serialized chain with an unambiguous identifier pair.
The ordinal is an offline correlation label, not a wire transaction ID.
Failed, incomplete, overlapping, or ambiguous chains remain unpaired.

Native CU and DU monotonic time is compared only under the documented
single-Docker-Linux-kernel clock assumption, without time namespaces. Host
controller monotonic time on Windows is a different domain and is not used
to order native events. F1 association epochs and cross-host clock
calibration are not implemented; reconnect/association-change experiments
need further instrumentation and review before stronger causal claims.

`white_box_available: true` means native F1 context state and at least one
correlated procedure are available. It does not mean complete lifecycle
coverage, a consistency verdict, or attack success. Shutdown can remove the
CU context while the DU process exits without a per-UE deletion event;
absence of that event is not proof of an orphan. Core/UE forced-stop and
log-tail limitations from the portable baseline still apply.

This version does not export actual DRB/RLC/MAC allocation tables, PDCP or
security state, implement settled-state invariants, or establish an S1–S6
attack. Attack outcomes remain `inconclusive`. These hooks are laboratory
transport-controlled instrumentation; a successful hook check is not a
demonstrated UE-only attack capability.
