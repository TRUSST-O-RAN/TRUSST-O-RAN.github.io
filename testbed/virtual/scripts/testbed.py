"""Prepare, check, smoke-test, and collect evidence for the OCUDU ZMQ lab.

`check` is offline unless --runtime is given. No command injects F1AP messages.
"""
from __future__ import annotations

import argparse
import configparser
from datetime import datetime, timezone
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import uuid
from functools import partial

import yaml

TESTBED = Path(__file__).resolve().parents[1]


def run(*args: str, cwd: Path = TESTBED, check: bool = True, env: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(args, cwd=cwd, check=check, text=True,
                          encoding="utf-8", errors="replace", capture_output=True, env=env)


def compose(*args: str, check: bool = True, artifacts: Path | None = None) -> subprocess.CompletedProcess:
    env = os.environ | {"TRUSST_TRACE_DIR": str(artifacts.resolve())} if artifacts else None
    return run("docker", "compose", "-f", str(TESTBED / "docker-compose.yml"),
               *args, check=check, env=env)


def read_env(path: Path) -> dict[str, str]:
    return dict(line.strip().split("=", 1) for line in path.read_text(encoding="utf-8").splitlines()
                if line.strip() and not line.lstrip().startswith("#"))


def device_args(value: str) -> dict[str, str]:
    return dict(item.split("=", 1) for item in value.split(","))


def validate_configuration(root: Path = TESTBED) -> list[str]:
    """Check cross-component contracts, not the full upstream CLI schema."""
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    try:
        stack = yaml.safe_load((root / "docker-compose.yml").read_text(encoding="utf-8"))
        cu = yaml.safe_load((root / "configs/gnb_cu.yml").read_text(encoding="utf-8"))
        du = yaml.safe_load((root / "configs/gnb_du.yml").read_text(encoding="utf-8"))
        ue = configparser.ConfigParser()
        ue.read_string((root / "configs/ue.conf").read_text(encoding="utf-8"))
        core = read_env(root / "configs/open5gs.env")
        core_config = yaml.safe_load((root / "configs/open5gs-5gc.yml.in").read_text(encoding="utf-8"))
        services = stack["services"]
        require("./configs/open5gs-5gc.yml.in:/open5gs/open5gs-5gc.yml.in:ro" in
                services["open5gs"]["volumes"], "Core must mount the lab's single-tracking-area template")
        require(cu["gnb_id"] == du["gnb_id"] and
                cu["gnb_id_bit_length"] == du["gnb_id_bit_length"],
                "CU and DU gNB identifiers and bit lengths must match")

        def address(service: str, network: str) -> str:
            return services[service]["networks"][network]["ipv4_address"]

        require(services["ocudu-cu"]["command"] == ["ocu", "-c", "/configs/gnb_cu.yml"],
                "CU must run ocu -c /configs/gnb_cu.yml")
        require(services["ocudu-du"]["command"] == ["odu", "-c", "/configs/gnb_du.yml"],
                "DU must run odu -c /configs/gnb_du.yml")
        require(services["srsue"]["command"] == ["srsue", "/configs/ue.conf"],
                "UE must run srsue /configs/ue.conf")
        require(cu["cu_cp"]["amf"]["addrs"] == core["OPEN5GS_IP"] == address("open5gs", "core"),
                "AMF target must match the core's reachable IP")
        require(core["UPF_ADVERTISE_IP"] == address("open5gs", "core"),
                "UPF must advertise its reachable core IP")
        require(cu["cu_cp"]["amf"]["bind_addrs"] == address("ocudu-cu", "core"),
                "CU N2 bind must match its core IP")
        require(cu["cu_up"]["ngu"]["socket"][0]["bind_addr"] == address("ocudu-cu", "core"),
                "CU N3 bind must match its core IP")
        require(cu["cu_cp"]["f1ap"]["bind_addrs"] == du["f1ap"]["addrs"] == address("ocudu-cu", "f1"),
                "DU F1-C target must match the CU F1 bind IP")
        require(du["f1ap"]["bind_addrs"] == address("ocudu-du", "f1"),
                "DU F1-C bind must match its F1 IP")
        for config, name, path in ((cu["cu_up"], "ocudu-cu", "CU"), (du, "ocudu-du", "DU")):
            require(config["f1u"]["socket"][0]["bind_addr"] == address(name, "f1"),
                    f"{path} F1-U bind must match its F1 IP")

        radio, terminal = device_args(du["ru_sdr"]["device_args"]), device_args(ue["rf"]["device_args"])
        require(du["ru_sdr"]["device_driver"] == ue["rf"]["device_name"] == "zmq", "Both radios must use ZMQ")
        require(radio["tx_port"] == terminal["rx_port"] and radio["rx_port"] == terminal["tx_port"],
                "ZMQ TX/RX endpoints must be crossed between DU and UE")
        require(radio["tx_port"].startswith(f'tcp://{address("ocudu-du", "rf")}:') and
                terminal["tx_port"].startswith(f'tcp://{address("srsue", "rf")}:') and
                radio["tx_port"] != terminal["tx_port"], "ZMQ TX endpoints must bind distinct owners' RF IPs")
        require(float(radio["base_srate"]) == float(terminal["base_srate"]) ==
                float(ue["rf"]["srate"]) == du["ru_sdr"]["srate"] * 1e6, "All RF sample rates must match")
        cell = du["cell_cfg"]
        require((cell["band"], cell["common_scs"], cell["channel_bandwidth_MHz"], cell["dl_arfcn"])
                == (3, 15, 10, 368500), "Reference srsUE cell must be band 3, 15 kHz, 10 MHz, ARFCN 368500")
        require(ue["rat.nr"]["bands"] == "3" and ue["rat.nr"]["nof_prb"] == "52" and
                ue["rat.nr"]["max_nof_prb"] == "52" and ue["rat.eutra"]["nof_carriers"] == "0",
                "srsUE must use NR band 3, 52 PRBs, and disable LTE")
        area = cu["cu_cp"]["amf"]["supported_tracking_areas"][0]
        plmn = area["plmn_list"][0]
        require(cell["plmn"] == plmn["plmn"] == core["MCC"] + core["MNC"], "PLMN must match at CU, DU, and core")
        require(cell["tac"] == area["tac"] == 7, "TAC must match the upstream core's TAC 7")
        areas = core_config["amf"]["tai"]
        require(len(areas) == 1 and areas[0]["tac"] == cell["tac"],
                "srsUE requires a single AMF tracking area matching the cell TAC")
        require(plmn["tai_slice_support_list"][0]["sst"] == 1, "Core slice requires SST 1")
        subscriber = core["SUBSCRIBER_DB"].split(",")
        require(subscriber[:4] == [ue["usim"]["imsi"], ue["usim"]["k"].lower(), "opc", ue["usim"]["opc"].lower()],
                "UE IMSI/K/OPc must match the provisioned subscriber")
        require(ue["usim"]["imsi"].startswith(cell["plmn"]), "Subscriber IMSI must use the cell PLMN")
        require(ipaddress.ip_address(subscriber[6]) in ipaddress.ip_network(core["UE_IP_BASE"] + ".0/24"),
                "Subscriber IP must be in the UPF tunnel subnet")
        require(ue["nas"]["apn"] == "internet", "UE APN must match the upstream core's internet DNN")
        for name in ("core", "f1", "rf"):
            subnet = ipaddress.ip_network(stack["networks"][name]["ipam"]["config"][0]["subnet"])
            ips = [address(service, name) for service in services if name in services[service]["networks"]]
            require(len(set(ips)) == len(ips), f"Duplicate service IP on {name}")
            require(all(ipaddress.ip_address(ip) in subnet for ip in ips), f"Service IP outside {name} subnet")
        for name, config in (("CU", cu), ("DU", du)):
            require("state_export" not in config.get("log", {}), f"{name}: upstream has no log.state_export")
            require("timers" not in config and "ru_cfg" not in config, f"{name}: unsupported legacy config block")
        require(all(not service.get("ports") for service in services.values()), "Lab services must not publish host ports")
    except (OSError, ValueError, KeyError, TypeError, IndexError, configparser.Error, yaml.YAMLError) as error:
        errors.append(f"Invalid testbed configuration: {error}")
    return errors


def source_errors() -> list[str]:
    errors = []
    versions = json.loads((TESTBED / "versions.json").read_text(encoding="utf-8"))
    for name in ("ocudu", "srsran4g"):
        path = TESTBED / "sources" / name
        if not (path / ".git").is_dir():
            errors.append(f"Missing {name} source; run python testbed/virtual/scripts/testbed.py prepare")
            continue
        if run("git", "rev-parse", "HEAD", cwd=path).stdout.strip() != versions[name]["commit"]:
            errors.append(f"{name} source does not match versions.json")
        if run("git", "status", "--porcelain", cwd=path).stdout.strip():
            errors.append(f"{name} source has local changes; preserve them before preparing a clean source directory")
    return errors


def prepare() -> None:
    versions = json.loads((TESTBED / "versions.json").read_text(encoding="utf-8"))
    for name in ("ocudu", "srsran4g"):
        path = TESTBED / "sources" / name
        if path.exists():
            continue  # Never reset or overwrite an existing checkout.
        path.mkdir(parents=True)
        spec = versions[name]
        run("git", "init", cwd=path)
        # These sources run inside Linux images, including shell entrypoints.
        run("git", "config", "core.autocrlf", "false", cwd=path)
        run("git", "remote", "add", "origin", spec["url"], cwd=path)
        run("git", "fetch", "--depth", "1", "origin", spec["commit"], cwd=path)
        run("git", "checkout", "--detach", spec["commit"], cwd=path)
    errors = source_errors()
    if errors:
        raise ValueError("; ".join(errors))
    (TESTBED / "artifacts/current").mkdir(parents=True, exist_ok=True)


def runtime_errors() -> list[str]:
    if not shutil.which("docker"):
        return ["Docker is not on PATH; use a Linux host/VM or Docker Desktop with a Linux backend"]
    errors = source_errors()
    info = run("docker", "info", "--format", "{{.OSType}}", check=False)
    if info.returncode or info.stdout.strip() != "linux":
        errors.append("A running Linux Docker daemon is required")
    version = run("docker", "compose", "version", "--short", check=False)
    match = re.match(r"v?(\d+)\.(\d+)", version.stdout.strip())
    if version.returncode or not match or tuple(map(int, match.groups())) < (2, 20):
        errors.append("Docker Compose 2.20 or later is required")
    rendered = compose("config", "--quiet", check=False)
    if rendered.returncode:
        errors.append("Docker Compose configuration failed: " + rendered.stderr.strip())
    return errors


def collect(destination: Path, *, status: str = "unclassified", artifacts: Path | None = None) -> Path:
    """Capture run provenance; no label or attack success is inferred from logs."""
    destination.mkdir(parents=True, exist_ok=False)
    raw = artifacts or Path(os.environ.get("TRUSST_TRACE_DIR", TESTBED / "artifacts/current"))
    if not raw.is_absolute():
        raw = TESTBED / raw
    env = os.environ | {"TRUSST_TRACE_DIR": str(raw.resolve())}
    commands = {
        "docker_version": ("docker", "version"),
        "docker_info": ("docker", "info"),
        "compose_config": ("docker", "compose", "config"),
        "containers": ("docker", "compose", "ps", "--all", "--format", "json"),
        "images": ("docker", "compose", "images", "--format", "json"),
        "logs": ("docker", "compose", "logs", "--no-color", "--timestamps"),
    }
    command_status = {}
    for name, args in commands.items():
        try:
            result = run(*args, check=False, env=env)
            (destination / f"{name}.txt").write_text(result.stdout + result.stderr, encoding="utf-8")
            command_status[name] = result.returncode
        except OSError as error:
            command_status[name] = str(error)
    shutil.copytree(TESTBED / "configs", destination / "configs")
    shutil.copytree(TESTBED / "docker", destination / "docker")
    shutil.copy(TESTBED / "versions.json", destination)
    shutil.copy(TESTBED / "docker-compose.yml", destination)
    shutil.copy(TESTBED / ".dockerignore", destination)
    if raw.is_dir():
        shutil.copytree(raw, destination / "raw")
    hashes = {str(path.relative_to(destination)): hashlib.sha256(path.read_bytes()).hexdigest()
              for path in sorted(destination.rglob("*")) if path.is_file()}
    metadata = {"captured_at": datetime.now(timezone.utc).isoformat(), "status": status,
                "evidence_kind": "runtime_capture", "commands": command_status, "sha256": hashes}
    try:
        metadata["source_errors"] = source_errors()
    except (OSError, subprocess.CalledProcessError) as error:
        metadata["source_errors"] = [str(error)]
    (destination / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return destination


def smoke(timeout: float, output: Path) -> bool:
    since = datetime.now(timezone.utc).isoformat()
    passed = False
    # New bind mounts keep old logs/PCAPs out of this run's evidence.
    artifacts = TESTBED / "artifacts" / ("smoke-" + str(uuid.uuid4()))
    artifacts.mkdir(parents=True)
    command = partial(compose, artifacts=artifacts)
    try:
        # Recreate processes so readiness cannot be satisfied by an old attach.
        command("up", "-d", "--no-build", "--force-recreate")
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            # This revision writes N2 readiness to its log sink. F1 and UE
            # session readiness are also printed on the console.
            cu_log = artifacts / "cu.log"
            cu = cu_log.read_text(encoding="utf-8", errors="replace") if cu_log.exists() else ""
            du = command("logs", "--since", since, "ocudu-du").stdout
            ue = command("logs", "--since", since, "srsue").stdout
            if (re.search(r"N2: Connection to AMF[^\n]*was established", cu) and
                    re.search(r"F1-C: Connection to CU-CP[^\n]*completed", du) and
                    "PDU Session Establishment successful" in ue):
                gateway = read_env(TESTBED / "configs/open5gs.env")["UE_IP_BASE"] + ".1"
                probe = command("exec", "-T", "srsue", "ping", "-I", "tun_srsue", "-c", "3", "-W", "2", gateway,
                                check=False)
                passed = probe.returncode == 0
                (artifacts / "ping.txt").write_text(
                    probe.stdout + probe.stderr + f"\nexit_code={probe.returncode}\n", encoding="utf-8")
                print(probe.stdout + probe.stderr)
                break
            time.sleep(2)
        if not passed:
            print("Smoke test failed: require N2, F1-C, UE PDU session, and tunnel ping.", file=sys.stderr)
    finally:
        # Stop writers before archiving; collected exit codes expose forced stops.
        command("stop", check=False)
        collect(output, status="benign_smoke_pass" if passed else "benign_smoke_fail", artifacts=artifacts)
        print(f"Evidence: {output}")
    return passed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("prepare", help="fetch pinned source commits without overwriting existing checkouts")
    check = sub.add_parser("check", help="validate cross-component configuration")
    check.add_argument("--runtime", action="store_true", help="also check Docker and pinned clean sources")
    smoke_parser = sub.add_parser("smoke", help="recreate stack, check benign attach/data, stop, and archive")
    smoke_parser.add_argument("--timeout", type=float, default=180)
    smoke_parser.add_argument("--output", type=Path)
    collect_parser = sub.add_parser("collect", help="archive logs/configs/provenance from the current stack")
    collect_parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "prepare":
            prepare()
            print("Pinned sources prepared.")
            return 0
        if args.command in ("check", "smoke"):
            errors = validate_configuration()
            if args.command == "smoke" or args.runtime:
                errors.extend(runtime_errors())
            if errors:
                for error in errors:
                    print(f"error: {error}", file=sys.stderr)
                return 2
            if args.command == "check":
                print("Configuration contracts passed." + (" Runtime prerequisites passed." if args.runtime else " Runtime not checked."))
                return 0
        output = args.output or TESTBED / "results" / ("testbed-" + str(uuid.uuid4()))
        if output.resolve().is_relative_to((TESTBED / "artifacts").resolve()):
            raise ValueError("Evidence output must be outside testbed/virtual/artifacts")
        if output.exists():
            raise ValueError(f"Evidence output already exists: {output}")
        if args.command == "smoke":
            if args.timeout <= 0:
                raise ValueError("--timeout must be positive")
            return 0 if smoke(args.timeout, output) else 1
        print(collect(output))
        return 0
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        detail = error.stderr if isinstance(error, subprocess.CalledProcessError) else str(error)
        print(f"testbed error: {detail}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
