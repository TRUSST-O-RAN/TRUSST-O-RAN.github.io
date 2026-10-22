# Live benign baseline, 2026-10-22

The live smoke test passed on Docker Desktop 4.96.1 with a WSL2 Linux backend
(kernel 6.18.54.1, 12 CPUs, approximately 16 GB RAM). SCTP bind/listen and
`/dev/net/tun` checks passed before the source builds.

Run [benign-baseline-20261022-02](https://github.com/TRUSST-O-RAN/thrust1-task1-cross-split-desynchronization/blob/main/results/benign-baseline-20261022-02/metadata.json)
completed at 07:01:45 America/Chicago (12:01:45 UTC). It established AMF/N2
and CU-DU/F1 connectivity, authenticated the UE, and established a PDU session
at `10.45.1.2`. The tunnel probe to `10.45.1.1` received 3 of 3 replies with
0% packet loss and 34.366 ms average RTT. All six evidence-collection commands
returned zero, and the pinned source check reported no errors. The smoke
command returned zero and stopped all four containers.

During cleanup, CU and DU exited with status 0; the core and UE reached Docker's
stop timeout and exited with status 137. The CU/DU PCAPs contain complete
records, but the core/UE log tails may not be fully flushed. This does not
invalidate the observed session and successful pings; graceful shutdown of
those two services remains a testbed limitation.

The run directory contains configurations, Dockerfiles, image identifiers,
Compose logs, and SHA-256 metadata. Its local `raw/` directory also contains
application logs, three protocol PCAPs, and `ping.txt` with the probe exit code.
Raw files are preserved locally and excluded from Git; retain the complete
directory for evidence review. Initial build logs are in the local ignored
`testbed/artifacts/build-20261022/` directory.

Run [benign-baseline-20261022-01](https://github.com/TRUSST-O-RAN/thrust1-task1-cross-split-desynchronization/blob/main/results/benign-baseline-20261022-01/metadata.json)
is retained as a failed infrastructure baseline. Authentication succeeded,
but the UE rejected the core's three-entry tracking-area list during
Registration Accept decoding. The retry uses the local single-TAC core
template. Preparation also required Linux shell line endings, restoration
of Windows-flattened upstream symbolic links, and matching CU/DU gNB IDs.

This is one benign connectivity observation. It demonstrates neither an
attack nor a CU/DU state inconsistency, timing precision, repeated reliability,
or completion of the research evaluation gates.
