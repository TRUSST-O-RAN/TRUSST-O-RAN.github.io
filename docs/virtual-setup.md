# Virtual CU/DU testbed

This lab follows the official [OCUDU CU/DU split tutorial](https://docs.ocudu.org/tutorials/cu_du_split/)
and [srsUE tutorial](https://docs.ocudu.org/tutorials/srsue/). It provides a benign
baseline for Task 1.1 before instrumenting internal state or running timing experiments.
The benign attach and tunnel-ping smoke test passed on Docker Desktop's WSL2
Linux backend on 2026-10-22. See the [run record](https://trusst-o-ran.github.io/validation.html).
A successful configuration check alone is not runtime validation.

```text
Open5GS <-- N2 (SCTP) / N3 (GTP-U) --> ocu
                                      |
                              F1-C (SCTP) / F1-U (GTP-U)
                                      |
                                     odu <-- ZeroMQ I/Q --> srsUE
```

ZeroMQ carries samples between the DU and UE. F1 connects CU and DU. There is
no third ZMQ synchronization socket. No SDR or spectrum access is needed.

## Requirements

- Linux x86-64 host or VM with AVX2 support, SCTP, and `/dev/net/tun`.
- Docker Engine with a Linux daemon and Compose 2.20 or later.
- Python 3.10+ with `pip install -r testbed/virtual/requirements.txt`, and Git.
- Budget at least 8 CPU cores, 16 GB RAM, and 30 GB disk for source builds;
  these are planning allowances, not measured minimum requirements.
- Internet access for initial sources, image builds, and dependencies.

Windows needs a Linux VM or Docker Desktop's WSL2 backend. PowerShell can
control a working Linux Docker daemon; changing shells does not add SCTP to
the daemon's kernel. If SCTP is unavailable in that kernel, use a Linux VM.
On a native Linux host check `test -c /dev/net/tun` and
`python3 -c 'import socket; socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_SCTP)'`.
Load the host SCTP module with `sudo modprobe sctp` if needed.

The core and UE receive `NET_ADMIN` and the TUN device inside their containers.
The RAN receives `SYS_NICE`; host CPU scheduling still affects timing precision.
The reference RAN image uses the `x86-64-v3` compiler target (AVX2).

## Prepare and validate

From the repository root:

```bash
python testbed/virtual/scripts/testbed.py check
python testbed/virtual/scripts/testbed.py prepare
python testbed/virtual/scripts/testbed.py check --runtime
docker compose -f testbed/virtual/docker-compose.yml build
```

`prepare` fetches the exact OCUDU and srsRAN 4G commits in
[versions.json](https://github.com/TRUSST-O-RAN/TRUSST-O-RAN.github.io/blob/main/testbed/virtual/versions.json) into ignored `sources/` directories. It refuses
to reset or overwrite an existing checkout with a different revision or local
changes. Preserve those changes before using a fresh source directory.
Open5GS v2.7.6 is built with the Docker context supplied by that pinned OCUDU
checkout, including its authentication functions and subscriber provisioning.
Source preparation disables Git's automatic CRLF conversion for Linux scripts;
the RAN Dockerfile restores the two upstream symbolic links flattened by Windows Git.

`check` verifies address bindings, F1 peers, crossed radio sockets, sample
rates, PLMN/TAC/slice, and subscriber credentials. `--runtime` also checks
clean pinned sources, a Linux Docker daemon, and Compose configuration parsing.
It does not execute OCUDU's full configuration parser or prove network readiness.

## Run the benign baseline

```bash
python testbed/virtual/scripts/testbed.py smoke --output results/benign-baseline-01
```

This recreates the containers from already-built images and waits for AMF
connectivity, F1-C connectivity, and a UE PDU session. It then pings the local
UPF tunnel gateway (`10.45.1.1`) through `tun_srsue`. It stops the stack to flush
packet captures and archives evidence on success or failure. The attach wait
defaults to 180 seconds after Compose startup; change it with `--timeout`.
The output directory must be new and outside `testbed/virtual/artifacts`.
Inspect recorded container exit codes: the observed run stopped CU/DU cleanly,
but Docker force-stopped the core and UE at its shutdown deadline. Their log
tails may be incomplete even when the connectivity smoke test passes.

Exit status: 0 means the benign connectivity check passed, 1 means a readiness
or ping failure, and 2 means invalid configuration, prerequisites, or command errors.
A smoke pass does not demonstrate a state inconsistency or white-box coverage.

For interactive operation:

```bash
docker compose -f testbed/virtual/docker-compose.yml up -d
docker compose -f testbed/virtual/docker-compose.yml logs -f ocudu-cu ocudu-du srsue
# Stop before collecting so PCAP buffers are flushed.
docker compose -f testbed/virtual/docker-compose.yml stop
python testbed/virtual/scripts/testbed.py collect --output results/manual-baseline-01
docker compose -f testbed/virtual/docker-compose.yml down
```

Startup dependencies are core health, CU's SCTP listener, DU process, then UE.
The DU may wait for the UE's ZMQ connection; do not require DU RF readiness
before starting the UE. Core health and a CU listener are startup gates only;
the smoke check verifies the resulting connectivity.

## Configuration and evidence

| Setting | Reference value |
|---|---|
| Core / CU N2-N3 | `10.53.1.2` / `10.53.1.3` |
| CU / DU F1 | `10.53.2.3` / `10.53.2.4` |
| DU / UE virtual radio | `10.53.3.4:2000` TX / `10.53.3.5:2001` TX |
| Radio | Band 3 FDD, 10 MHz, 15 kHz SCS, 52 PRBs, 11.52 Msamples/s |
| PLMN / TAC / slice | `00101` / `7` / SST `1` |
| UE / gateway / DNN | `10.45.1.2` / `10.45.1.1` / `internet` |

[ue.conf](https://github.com/TRUSST-O-RAN/TRUSST-O-RAN.github.io/blob/main/testbed/virtual/configs/ue.conf) and [open5gs.env](https://github.com/TRUSST-O-RAN/TRUSST-O-RAN.github.io/blob/main/testbed/virtual/configs/open5gs.env) contain the
same public test IMSI, K, and OPc. The container provides the UE's network
namespace; no host `ue1` namespace is required. Bind addresses are specific
container addresses so advertised GTP-U endpoints remain reachable.

The pinned upstream `docker/open5gs/setup_tun.py` creates `ogstun` repeatedly
inside a 256-iteration loop. Compose mounts [our helper](https://github.com/TRUSST-O-RAN/TRUSST-O-RAN.github.io/blob/main/testbed/virtual/docker/setup_tun.py)
over it to create one tunnel and one connected subnet. No NAT or Internet
data-network service is configured by this helper. The core image still has
its normal bridge egress; this is a local test network, not an air gap.

The core also mounts [a lab-specific template](https://github.com/TRUSST-O-RAN/TRUSST-O-RAN.github.io/blob/main/testbed/virtual/configs/open5gs-5gc.yml.in)
that advertises only TAC 7. The upstream template adds TACs 8 and 9 for its NTN
example, but the pinned srsUE decoder rejects the resulting multi-entry TAI list.
CU and DU explicitly share gNB ID 1 with a 22-bit identifier. UE PHY-library
logging is limited to warnings to avoid logging every PDCCH candidate.

Manual-run outputs are in ignored `artifacts/current/`. Each smoke run uses a
fresh `artifacts/smoke-<id>/` bind mount to keep logs and PCAPs separate:

- `cu.log`, `du.log`, `ue.log`: stock application logs.
- `cu_ngap.pcap`, `cu_f1ap.pcap`, `du_f1ap.pcap`: protocol captures.

Collected runs include raw files, Compose logs, configurations, Dockerfiles,
source version pins, image identifiers, command exit statuses, and SHA-256
hashes. Keep the complete output directory. Base image tags and OS package
repositories can change; archive the built images for exact binary replay.
Source pinning alone does not promise bit-for-bit reproducible images.

Stock OCUDU does not export normalized CU/DU state automatically. Task 1
provides the separate analysis and instrumentation tooling. See the
[validation gates](https://trusst-o-ran.github.io/evaluation.html).

## Tuning and troubleshooting

- AMF/F1 failures: inspect `logs` and `docker compose ... ps --all`, confirm
  SCTP support in the Docker host, and check that the private subnets do not
  overlap existing routes. If changing addresses, update Compose and YAML/INI
  together, then rerun `check`.
- No RF samples: verify opposite TX/RX endpoints and matching sample rates;
  start the UE while the DU waits. Avoid competing processes on the sockets.
- Authentication failure: compare UE credentials and the provisioned subscriber.
  `docker compose ... down -v` deletes the lab subscriber volume; preserve
  evidence first. Recreating the containers preserves that volume by default.
- Build/link errors: retain build logs. The srsUE image disables dynamic RF
  plugins so its radio driver is linked into the executable copied to runtime.
- Edited configurations: use `docker compose ... up -d --force-recreate`.
  An unchanged Compose service is not necessarily restarted by `up -d` alone.
- Supported timing controls must come from the pinned source/schema. CU
  `cu_cp.inactivity_timer` is in seconds. RRC T310/T311 are broadcast under
  `cell_cfg.sib.t310` and `cell_cfg.sib.t311` (milliseconds); verify values against
  the configuration reference before experimentation. The previous top-level
  `timers.*_ms`, `ru_cfg`, and `log.state_export` blocks were unsupported.

## Scope across tasks

This identical baseline is distributed to every organization repository. It
provides an Open5GS core, split CU/DU, one provisioned srsUE, virtual RF, and
benign connectivity/evidence automation. Run one copy at a time on a Docker
daemon: the Compose project, images, and subnets are shared defaults.

- Task 1: baseline for F1 lifecycle and context experiments; internal state
  instrumentation and procedure hooks are separate task-specific work.
- Task 2: no split-7.2 RU, eCPRI transport, or programmable HARQ impairment.
- Task 3: no near-real-time RIC, E2/KPM pipeline, or xApp.
- Task 4: no selective MSG3/MSG4/MSG5 suppression in the stock UE.

Those task-specific extensions must be implemented and measured separately.
The shared copy contains infrastructure only; attack runners stay in their
task repositories. The source revision and file hashes are recorded in
`shared-manifest.json`; see the central documentation for synchronization.

## References

- [OCUDU CU/DU split](https://docs.ocudu.org/tutorials/cu_du_split/)
- [OCUDU srsUE integration](https://docs.ocudu.org/tutorials/srsue/)
- [OCUDU installation and ZMQ build](https://docs.ocudu.org/user_manual/installation/)
- [Pinned OCUDU source](https://gitlab.com/ocudu/ocudu/-/tree/a785384da53b325174142ff503dbd4d222b233d0)
- [Pinned srsRAN 4G source](https://github.com/srsran/srsRAN_4G/tree/eea87b1d893ae58e0b08bc381730c502024ae71f)
