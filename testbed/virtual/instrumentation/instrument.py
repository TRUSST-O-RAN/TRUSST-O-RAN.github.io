"""Build and control the shared instrumented virtual testbed."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from testbed.virtual.scripts import testbed as lab
from testbed.virtual.instrumentation.state import analyze

HERE = Path(__file__).resolve().parent
IMAGE = "trusst/ocudu-zmq:instrumented"
BUILD_FILES = ("ocudu.Dockerfile", "ocudu.patch", "source-files.sha256", "trusst_lab.h")


def fingerprint() -> str:
    digest = hashlib.sha256()
    for name in BUILD_FILES:
        # Git checkouts can use CRLF; Docker and the digest use canonical LF.
        digest.update(name.encode() + b"\0" + (HERE / name).read_bytes().replace(b"\r\n", b"\n") + b"\0")
    return digest.hexdigest()


def validate(config: dict) -> dict:
    if not isinstance(config, dict) or set(config) - {"setup_ms", "modification_ms", "release_ms", "inactivity_s", "arm_after_baseline"}:
        raise ValueError("Unknown instrumentation setting")
    for name, value in config.items():
        if name == "arm_after_baseline":
            if type(value) is not bool:
                raise ValueError("arm_after_baseline must be a boolean")
            continue
        low, high = (5, 120) if name == "inactivity_s" else (0, 2000)
        if type(value) is not int or not low <= value <= high:
            raise ValueError(f"instrumentation.{name} must be an integer from {low} to {high}")
    return dict(config)


def environment(artifacts: Path, run_id: str, hooks: dict) -> dict:
    return os.environ | {"TRUSST_TRACE_DIR": str(artifacts.resolve()), "TRUSST_RUN_ID": run_id,
        "TRUSST_CU_CONFIG": "/traces/instrumented-cu.yml" if "inactivity_s" in hooks else "/configs/gnb_cu.yml",
        **{f"TRUSST_HOOK_{name.upper()}_MS": "0" if hooks.get("arm_after_baseline") else str(hooks.get(f"{name.lower()}_ms", 0))
           for name in ("SETUP", "MODIFICATION", "RELEASE")}}


def write_configuration(artifacts: Path, hooks: dict) -> None:
    if "inactivity_s" in hooks:
        cu = yaml.safe_load((lab.TESTBED / "configs/gnb_cu.yml").read_text(encoding="utf-8"))
        cu["cu_cp"]["inactivity_timer"] = hooks["inactivity_s"]
        (artifacts / "instrumented-cu.yml").write_text(yaml.safe_dump(cu, sort_keys=False), encoding="utf-8")


def arm_hooks(artifacts: Path, hooks: dict) -> None:
    target = artifacts/"hooks"
    target.mkdir()
    for name in ("setup", "modification", "release"):
        path = target/(name.upper()+".ms")
        temporary = target/(name.upper()+".tmp")
        temporary.write_text(str(hooks.get(name+"_ms", 0))+"\n", encoding="ascii", newline="\n")
        temporary.replace(path)


def compose(*args: str, artifacts: Path, run_id: str, hooks: dict, check: bool = True):
    return lab.run("docker", "compose", "-f", str(lab.TESTBED / "docker-compose.yml"),
                   "-f", str(HERE / "compose.yml"), *args, check=check,
                   env=environment(artifacts, run_id, hooks))


def verify_image() -> dict:
    image = json.loads(lab.run("docker", "image", "inspect", IMAGE).stdout)[0]
    labels = image.get("Config", {}).get("Labels", {}) or {}
    if labels.get("org.trusst.instrumentation.sha256") != fingerprint():
        raise ValueError("Instrumented image does not match current patch/header; run instrument.py build")
    return {"image_id": image["Id"], "instrumentation_sha256": fingerprint(), "labels": labels}


def build() -> None:
    errors = lab.source_errors()
    if errors:
        raise ValueError("; ".join(errors))
    commands = [["docker", "build", "--build-arg", "BUILD_JOBS=6", "--build-arg",
                 f"INSTRUMENTATION_SHA256={fingerprint()}", "-t", IMAGE, "-f", "instrumentation/ocudu.Dockerfile", "."]]
    for command in commands:
        subprocess.run(command, cwd=lab.TESTBED, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("build")
    report = commands.add_parser("report")
    report.add_argument("directory", type=Path)
    report.add_argument("--run-id", required=True)
    run = commands.add_parser("run", help="Run a lifecycle scenario; defaults to the benign instrumented control")
    run.add_argument("scenario", type=Path, nargs="?", default=HERE.parent/"scenarios/control.yaml")
    run.add_argument("--output", type=Path, default=HERE.parent/"traces")
    check = commands.add_parser("check", help="Recheck a captured settled-state window")
    check.add_argument("directory", type=Path)
    args = parser.parse_args()
    if args.command == "build":
        build()
    elif args.command == "run":
        from testbed.virtual.instrumentation.runner import VirtualScenarioRunner
        scenario = yaml.safe_load(args.scenario.read_text(encoding="utf-8"))
        result = VirtualScenarioRunner(scenario, args.scenario, args.output).run()
        print(json.dumps(result, indent=2))
        return 0 if result["execution_completed"] else 1
    elif args.command == "check":
        from testbed.virtual.instrumentation.consistency import check
        window = json.loads((args.directory/"validation-window.json").read_text(encoding="utf-8"))
        result = check(args.directory, window["run_id"], window["start_ns"], window["end_ns"])
        print(json.dumps(result, indent=2))
        return 0 if result["outcome"] == "no_inconsistency_observed" else 1
    else:
        result = analyze(args.directory, args.run_id)
        print(json.dumps(result, indent=2))
        return 0 if result["white_box_available"] else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
