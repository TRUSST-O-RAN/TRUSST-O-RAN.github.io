# Virtual testbed

Open5GS → OCUDU CU/DU → srsUE, with ZeroMQ replacing the radio link. No SDR is needed.
This lab is shared by all four tasks. Run one copy at a time on a Docker daemon.

## Requirements

- Linux Docker Engine and Compose 2.20+, or Docker Desktop with WSL2.
- x86-64 with AVX2, SCTP, and `/dev/net/tun`.
- Python 3.10+, Git, about 16 GB RAM and 30 GB free disk for builds.

Docker must be on your shell's `PATH`. On Windows, select Docker's Linux backend.

## Setup

Run from the repository root:

```text
python -m pip install -r testbed/virtual/requirements.txt
python testbed/virtual/scripts/testbed.py prepare
python testbed/virtual/scripts/testbed.py check --runtime
docker compose -f testbed/virtual/docker-compose.yml build
python testbed/virtual/instrumentation/instrument.py build
```

The first build takes several minutes. Sources are pinned in `versions.json`.
The instrumentation patch is applied inside Docker; the source checkout stays clean.

## Test

```text
python testbed/virtual/instrumentation/instrument.py run
```

This creates a fresh stack, verifies attachment and tunnel traffic, compares CU/DU
context inventories, stops the stack, and saves evidence under `testbed/virtual/traces/`.
The [instrumentation guide](instrumentation.md) describes hooks and results.

For the original connectivity-only test:

```text
python testbed/virtual/scripts/testbed.py smoke --output traces/benign
```

## Scope

The lab has one fixed subscriber and no published host ports. Shared instrumentation
tracks F1 contexts; each task still needs its own radio, resource, or RIC observations.
Task 2 needs RU/HARQ measurements, Task 3 needs E2/RIC, and Task 4 needs selective
random-access controls. A passing control is not a demonstrated attack.

CU/DU stop cleanly. Core/UE can reach Docker's stop timeout, leaving incomplete log
tails; exit codes are retained with each run. Logs and captures stay local by default.

[OCUDU split guide](https://docs.ocudu.org/tutorials/cu_du_split/) · [srsUE guide](https://docs.ocudu.org/tutorials/srsue/)
