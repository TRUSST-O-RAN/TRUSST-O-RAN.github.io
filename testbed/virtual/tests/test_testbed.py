"""Offline regression checks for lab wiring and evidence gating."""
from __future__ import annotations

import importlib.util
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from unittest.mock import patch

import pytest
import yaml

from testbed.virtual.scripts import testbed


@pytest.fixture
def lab(tmp_path):
    shutil.copytree(testbed.TESTBED / "configs", tmp_path / "configs")
    shutil.copy(testbed.TESTBED / "docker-compose.yml", tmp_path)
    return tmp_path


def change(root, name, update):
    path = root / "configs" / name
    config = yaml.safe_load(path.read_text())
    update(config)
    path.write_text(yaml.safe_dump(config))


def test_reference_configuration():
    assert testbed.validate_configuration() == []


def test_shared_bundle_hashes():
    manifest = json.loads((testbed.TESTBED / "shared-manifest.json").read_text(encoding="utf-8"))
    for name, digest in manifest["files"].items():
        assert hashlib.sha256((testbed.TESTBED / name).read_bytes()).hexdigest() == digest, name


@pytest.mark.parametrize("name,update,message", [
    ("gnb_du.yml", lambda c: c.update(gnb_id=411), "gNB identifiers"),
    ("gnb_du.yml", lambda c: c.update(gnb_id_bit_length=24), "gNB identifiers"),
    ("open5gs-5gc.yml.in", lambda c: c["amf"]["tai"].append({"tac": 8}), "single AMF tracking area"),
    ("open5gs-5gc.yml.in", lambda c: c["amf"]["tai"][0].update(tac=8), "single AMF tracking area"),
    ("gnb_cu.yml", lambda c: c["cu_up"]["ngu"]["socket"][0].update(bind_addr="127.0.0.1"), "N3 bind"),
    ("gnb_cu.yml", lambda c: c["cu_cp"]["f1ap"].update(bind_addrs="0.0.0.0"), "F1-C target"),
    ("gnb_du.yml", lambda c: c["f1u"]["socket"][0].update(bind_addr="127.0.0.1"), "F1-U bind"),
    ("gnb_du.yml", lambda c: c["ru_sdr"].update(srate=23.04), "sample rates"),
    ("gnb_du.yml", lambda c: c["ru_sdr"].update(device_args="tx_port=tcp://10.53.3.4:2001,rx_port=tcp://10.53.3.5:2000,base_srate=11.52e6"), "crossed"),
    ("gnb_du.yml", lambda c: c["cell_cfg"].update(plmn="99999"), "PLMN"),
    ("gnb_du.yml", lambda c: c["cell_cfg"].update(tac=1), "TAC"),
    ("gnb_du.yml", lambda c: c["log"].update(state_export={"enabled": True}), "state_export"),
])
def test_broken_component_contracts(lab, name, update, message):
    change(lab, name, update)
    assert any(message in error for error in testbed.validate_configuration(lab))


def test_wrong_subscriber_key(lab):
    path = lab / "configs/ue.conf"
    path.write_text(path.read_text().replace("00112233445566778899aabbccddeeff", "0" * 32))
    assert any("IMSI/K/OPc" in error for error in testbed.validate_configuration(lab))


def test_subscriber_outside_tunnel_subnet(lab):
    path = lab / "configs/open5gs.env"
    path.write_text(path.read_text().replace("UE_IP_BASE=10.45.1", "UE_IP_BASE=10.45.0"))
    assert any("UPF tunnel subnet" in error for error in testbed.validate_configuration(lab))


def test_malformed_config(lab):
    (lab / "configs/gnb_du.yml").write_text("invalid: [")
    assert testbed.validate_configuration(lab)[0].startswith("Invalid testbed configuration")










@pytest.mark.parametrize("ping_code,expected", [(0, True), (1, False)])
def test_smoke_requires_data_plane_and_archives_outcome(tmp_path, lab, ping_code, expected):
    def fake_compose(*args, **kwargs):
        text = ""
        code = 0
        if args[0] == "up":
            (kwargs["artifacts"] / "cu.log").write_text("N2: Connection to AMF on 10.53.1.2:38412 was established\n")
        if args[0] == "logs":
            text = {
                "ocudu-cu": "N2: Connection to AMF on 10.53.1.2:38412 completed",
                "ocudu-du": "F1-C: Connection to CU-CP on 10.53.2.3:38472 completed",
                "srsue": "PDU Session Establishment successful. IP: 10.45.1.2",
            }[args[-1]]
        if args[0] == "exec":
            code = ping_code
        return subprocess.CompletedProcess(args, code, text, "")

    with patch.object(testbed, "TESTBED", tmp_path), \
            patch.object(testbed, "compose", side_effect=fake_compose) as command, \
            patch.object(testbed, "collect") as collect:
        assert testbed.smoke(1, tmp_path / "evidence") is expected
    assert collect.call_count == 1
    assert collect.call_args.kwargs["status"] == ("benign_smoke_pass" if expected else "benign_smoke_fail")
    artifacts = next(call.kwargs["artifacts"] for call in command.call_args_list if call.args[0] == "up")
    assert f"exit_code={ping_code}" in (artifacts / "ping.txt").read_text()
    assert any(call.args == ("stop",) and call.kwargs["check"] is False for call in command.call_args_list)
    assert all("--since" in call.args for call in command.call_args_list if call.args[0] == "logs")


def test_tunnel_setup_creates_one_interface():
    spec = importlib.util.spec_from_file_location("setup_tun", testbed.TESTBED / "docker/setup_tun.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with patch.object(module.subprocess, "run") as command:
        module.setup("ogstun", "10.45.1.0/24")
    assert command.call_count == 3
    assert command.call_args_list[0].args[0] == ["ip", "tuntap", "add", "dev", "ogstun", "mode", "tun"]
    assert command.call_args_list[1].args[0] == ["ip", "address", "add", "10.45.1.1/24", "dev", "ogstun"]
