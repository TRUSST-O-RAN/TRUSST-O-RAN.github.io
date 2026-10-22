"""Bounded lifecycle controls on the shared local virtual lab.

This backend observes real commands, console events, and traffic. It does not
fabricate F1AP messages or infer internal CU/DU state from command completion.
"""
from __future__ import annotations

from datetime import datetime, timezone
from functools import partial
import json
import math
from pathlib import Path
import random
import re
import shutil
import subprocess
import time
import uuid

from testbed.virtual.scripts import testbed as lab
from testbed.virtual.instrumentation import instrument
from testbed.virtual.instrumentation.state import analyze as analyze_state, read_records
from testbed.virtual.instrumentation.consistency import check as check_contexts, read_inventories


def validate_plan(scenario: dict) -> dict:
    if not isinstance(scenario, dict) or not isinstance(scenario.get("virtual", {}), dict):
        raise ValueError("A scenario and its virtual configuration must be mappings")
    config = dict(scenario.get("virtual", {}))
    if config.get("action") == "ue_rlf":
        raise ValueError("The pinned UE rlf console triggers LTE RRC, not NR; NR RLF validation is unavailable")
    if config.get("action") not in {"observe", "ue_idle_release", "ue_restart"}:
        raise ValueError("The virtual backend requires virtual.action: observe, ue_idle_release or ue_restart; F1 injection plans need endpoint hooks")
    if "instrumentation" in config:
        config["instrumentation"] = instrument.validate(config["instrumentation"])
    if config.get("action") == "ue_idle_release" and "inactivity_s" not in config.get("instrumentation", {}):
        raise ValueError("ue_idle_release requires instrumented inactivity_s configuration")
    sources = scenario.get("sources", {})
    if (not isinstance(sources, dict) or type(sources.get("count", 1)) is not int
            or sources.get("count", 1) != 1 or sources.get("identity_mode", "fixed") != "fixed"):
        raise ValueError("This baseline supports one provisioned UE with fixed identity; concurrent sources and rotation are unavailable")
    cycles = config.get("cycles", 1)
    if type(cycles) is not int or not 1 <= cycles <= 5:
        raise ValueError("virtual.cycles must be an integer between 1 and 5")
    timeout = config.get("timeout_s", 60)
    settling = config.get("settling_s", 2)
    for name, value, low, high in (("timeout_s", timeout, 5, 180), ("settling_s", settling, 0, 20)):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not low <= value <= high:
            raise ValueError(f"virtual.{name} must be between {low} and {high}")
    config.update(cycles=cycles, timeout_s=timeout, settling_s=settling)
    duration = config.get("state_window_s", 3)
    if type(duration) is not int or not 2 <= duration <= 10:
        raise ValueError("virtual.state_window_s must be an integer from 2 to 10")
    config["state_window_s"] = duration
    return config


class VirtualScenarioRunner:
    def __init__(self, scenario: dict, scenario_path: Path, output_root: Path, offset_ns: int | None = None):
        self.scenario = scenario
        self.config = validate_plan(scenario)
        timing = scenario.get("timing", {})
        self.offset_ns = timing.get("offset_ns", 0) if offset_ns is None else offset_ns
        self.jitter_ns = timing.get("jitter_std_ns", 0)
        for name, value in (("offset_ns", self.offset_ns), ("jitter_std_ns", self.jitter_ns)):
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 1_000_000_000:
                raise ValueError(f"{name} must be finite and between 0 and 1000000000")
        self.seed = timing.get("seed", 0)
        if type(self.seed) is not int:
            raise ValueError("timing.seed must be an integer")
        self.random = random.Random(self.seed)
        self.ping_attempts: dict[str, int] = {}
        self.scenario_path = scenario_path
        run_id = str(uuid.uuid4())
        self.output = output_root.resolve() / ("virtual-" + run_id)
        if self.output.is_relative_to((lab.TESTBED / "artifacts").resolve()):
            raise ValueError("Scenario output must be outside the virtual lab artifacts directory")
        self.artifacts = lab.TESTBED / "artifacts" / ("scenario-" + run_id)
        self.command = partial(lab.compose, artifacts=self.artifacts)
        self.instrumented = "instrumentation" in self.config
        if self.instrumented:
            self.command = partial(instrument.compose, artifacts=self.artifacts, run_id=run_id,
                                   hooks=self.config["instrumentation"])
        self.result = {"scenario_id": scenario.get("scenario_id", "unknown"), "run_id": run_id,
                       "backend": "virtual", "evidence_kind": "runtime_observation",
                       "capability": "ue_lifecycle", "source_count": 1, "identity_mode": "fixed",
                       "action": self.config["action"], "seed": self.seed,
                       "offset_ns": self.offset_ns, "jitter_std_ns": self.jitter_ns,
                       "status": "infrastructure_failure", "execution_completed": False,
                       "success": False, "attack_outcome": "inconclusive",
                       "white_box_available": False, "cycles": [], "output": str(self.output)}

    def event(self, event: str, **fields) -> None:
        record = {"event": event, "timestamp_ns": time.time_ns(), "monotonic_ns": time.monotonic_ns(),
                  "observation_kind": "experiment_or_console", **fields}
        with (self.artifacts / "events.jsonl").open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(record) + "\n")

    def logs(self, service: str, since: str) -> str:
        return self.command("logs", "--since", since, "--timestamps", service).stdout

    def wait_for(self, predicate, description: str, timeout: float | None = None) -> None:
        deadline = time.monotonic() + (timeout or self.config["timeout_s"])
        while time.monotonic() < deadline:
            if predicate():
                return
            time.sleep(0.5)
        raise TimeoutError(description)

    def ping(self, label: str) -> bool:
        gateway = lab.read_env(lab.TESTBED / "configs/open5gs.env")["UE_IP_BASE"] + ".1"
        probe = self.command("exec", "-T", "srsue", "ping", "-I", "tun_srsue", "-c", "3", "-W", "2", gateway, check=False)
        self.ping_attempts[label] = self.ping_attempts.get(label, 0) + 1
        attempt = self.ping_attempts[label]
        (self.artifacts / f"{label}-ping-{attempt}.txt").write_text(
            probe.stdout + probe.stderr + f"\nexit_code={probe.returncode}\n", encoding="utf-8")
        self.event("tunnel_ping", label=label, attempt=attempt, exit_code=probe.returncode)
        return probe.returncode == 0

    def observe_state(self, cycle: int) -> dict:
        latest = {}
        def samples_ready():
            try:
                rows = read_inventories(self.artifacts, self.result["run_id"])
                latest.update({component: records[-1]["monotonic_ns"] for component, records in rows.items()})
                return True
            except (OSError, ValueError):
                return False
        self.wait_for(samples_ready, "Native inventories unavailable", timeout=5)
        start = max(latest.values())
        end = start + self.config["state_window_s"] * 1_000_000_000
        self.wait_for(lambda: samples_ready() and min(latest.values()) >= end,
                      "Native inventory sampling stalled", timeout=self.config["state_window_s"]+5)
        window = {"run_id": self.result["run_id"], "start_ns": start, "end_ns": end}
        (self.artifacts / "validation-window.json").write_text(json.dumps(window)+"\n", encoding="utf-8")
        (self.artifacts / f"cycle-{cycle}-validation-window.json").write_text(json.dumps(window)+"\n", encoding="utf-8")
        report = check_contexts(self.artifacts, self.result["run_id"], start, end)
        name = f"cycle-{cycle}-context-check.json"
        (self.artifacts / name).write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
        self.event("state_window_completed", cycle=cycle, native_start_ns=start, native_end_ns=end,
                   state_outcome=report["outcome"])
        return {"state_outcome": report["outcome"], "state_report": "raw/"+name}

    def run(self) -> dict:
        errors = lab.validate_configuration() + lab.runtime_errors()
        if errors:
            raise ValueError("; ".join(errors))
        self.artifacts.mkdir(parents=True)
        shutil.copyfile(self.scenario_path, self.artifacts / "scenario.yaml")
        shutil.copyfile(Path(__file__), self.artifacts / "backend.py")
        since = datetime.now(timezone.utc).isoformat()
        self.result["started_at"] = since
        try:
            if self.instrumented:
                provenance = instrument.verify_image()
                instrument.write_configuration(self.artifacts, self.config["instrumentation"])
                (self.artifacts / "instrumented-image.json").write_text(json.dumps(provenance, indent=2)+"\n", encoding="utf-8")
                evidence = self.artifacts / "instrumentation"
                evidence.mkdir()
                for name in (*instrument.BUILD_FILES, "compose.yml", "instrument.py", "state.py", "consistency.py"):
                    shutil.copyfile(instrument.HERE / name, evidence / name)
                effective = self.command("config").stdout
                (self.artifacts / "effective-compose.yml").write_text(effective, encoding="utf-8")
            self.event("stack_start_requested")
            self.command("up", "-d", "--no-build", "--force-recreate")

            def ready():
                path = self.artifacts / "cu.log"
                cu = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
                return (re.search(r"N2: Connection to AMF[^\n]*was established", cu)
                        and "F1-C: Connection to CU-CP" in self.logs("ocudu-du", since)
                        and "PDU Session Establishment successful" in self.logs("srsue", since))

            self.wait_for(ready, "Baseline N2/F1/PDU session readiness timed out")
            if not self.ping("baseline"):
                raise RuntimeError("Baseline tunnel traffic failed before perturbation")
            self.event("baseline_ready")
            if self.instrumented and self.config["instrumentation"].get("arm_after_baseline"):
                instrument.arm_hooks(self.artifacts, self.config["instrumentation"])
                self.event("hooks_armed")
            for cycle in range(1, self.config["cycles"] + 1):
                delay_ns = min(1_000_000_000, max(0, round(self.offset_ns + self.random.gauss(0, self.jitter_ns))))
                requested_at = time.monotonic_ns()
                time.sleep(delay_ns / 1e9)
                started_at = time.monotonic_ns()
                boundary = datetime.now(timezone.utc).isoformat()
                ue_log = self.artifacts / "ue.log"
                if ue_log.exists():
                    shutil.copyfile(ue_log, self.artifacts / f"cycle-{cycle}-before-ue.log")
                self.event("perturbation_started", cycle=cycle, action=self.config["action"],
                           requested_delay_ns=delay_ns, observed_host_wait_ns=started_at-requested_at)
                fresh_session = None
                if self.config["action"] == "ue_restart":
                    self.command("restart", "--timeout", "2", "srsue")
                    try:
                        self.wait_for(lambda: "PDU Session Establishment successful" in self.logs("srsue", boundary),
                                      "The restarted UE did not establish a fresh PDU session")
                        fresh_session = True
                    except TimeoutError:
                        fresh_session = False
                        self.event("reconnect_session_timeout", cycle=cycle)
                elif self.config["action"] == "ue_idle_release":
                    def release_finished():
                        try:
                            rows = read_records(self.artifacts, self.result["run_id"])
                            return all(sum(r["component"] == component and r["procedure"] == "RELEASE"
                                and r["event"] in {"procedure_success", "procedure_failure"} for r in rows) >= cycle
                                for component in ("CU", "DU"))
                        except (OSError, ValueError):
                            return False
                    self.wait_for(release_finished, "The idle UE release did not finish on both endpoints")
                    self.event("inactivity_release_observed", cycle=cycle)
                self.event("perturbation_observed", cycle=cycle, action=self.config["action"])
                time.sleep(self.config["settling_s"])
                validation = self.observe_state(cycle) if self.instrumented else {}
                deadline = time.monotonic() + (self.config["timeout_s"] if fresh_session is not False else 0)
                recovered = self.ping(f"cycle-{cycle}")
                while not recovered and time.monotonic() < deadline:
                    time.sleep(1)
                    recovered = self.ping(f"cycle-{cycle}")
                observed = self.logs("srsue", boundary)
                (self.artifacts / f"cycle-{cycle}-console.txt").write_text(observed, encoding="utf-8")
                self.result["cycles"].append({"cycle": cycle, "requested_delay_ns": delay_ns,
                    "observed_host_wait_ns": started_at-requested_at,
                    "action_elapsed_ns": time.monotonic_ns()-started_at,
                    "connectivity_recovered": recovered, "fresh_session_established": fresh_session, **validation})
                if not recovered:
                    self.result["stopped_after_recovery_failure"] = True
                    break
            self.result.update(status="inconclusive", execution_completed=True)
        except (OSError, ValueError, RuntimeError, TimeoutError, subprocess.SubprocessError) as error:
            detail = error.stderr if isinstance(error, subprocess.CalledProcessError) else str(error)
            self.result["error"] = detail
            self.event("execution_error", error=detail)
        finally:
            self.event("stack_stop_requested")
            try:
                stopped = self.command("stop", check=False)
                self.result["stop_command_exit_code"] = stopped.returncode
            except OSError as error:
                self.result["cleanup_error"] = str(error)
            self.result["finished_at"] = datetime.now(timezone.utc).isoformat()
            if self.instrumented:
                state = analyze_state(self.artifacts, self.result["run_id"])
                requested_hooks = {name.removesuffix("_ms").upper(): value
                                   for name, value in self.config["instrumentation"].items() if name.endswith("_ms") and value}
                state["requested_hooks"] = requested_hooks
                state["unobserved_hooks"] = [name for name, delay in requested_hooks.items()
                    if not any(h["procedure"] == name and h["delay_ms"] == delay
                               and h["elapsed_ns"] >= max(0, delay-2)*1_000_000 for h in state.get("hooks", []))]
                if state["unobserved_hooks"]:
                    state["errors"].append("Requested hooks did not complete with the configured delay")
                    state["white_box_available"] = False
                self.result["white_box_available"] = state["white_box_available"]
                self.result["instrumentation_scope"] = state["scope"]
                self.result["state_report"] = "raw/state-report.json"
                self.result["capability"] = "f1_context_instrumentation"
                (self.artifacts / "state-report.json").write_text(json.dumps(state, indent=2)+"\n", encoding="utf-8")
                if not state["white_box_available"]:
                    self.result.update(status="infrastructure_failure", execution_completed=False,
                                       instrumentation_error="Native state correlation coverage unavailable; see state-report.json")
            (self.artifacts / "scenario-result.json").write_text(json.dumps(self.result, indent=2)+"\n", encoding="utf-8")
            lab.collect(self.output, status=self.result["status"], artifacts=self.artifacts)
            (self.output / "result.json").write_text(json.dumps(self.result, indent=2)+"\n", encoding="utf-8")
        return self.result
