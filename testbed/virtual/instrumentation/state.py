"""Validate native F1 state exports and report bounded correlation coverage.

This is instrumentation diagnostics, not a desynchronization verdict/checker.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import json
from pathlib import Path

SCHEMA = "trusst.f1-state.v1"
PROCEDURES = {"SETUP", "MODIFICATION", "RELEASE"}
EVENTS = {"context_created", "context_deleted", "identity_bound", "rrc_state_changed",
          "release_marked", "procedure_send", "procedure_begin", "procedure_success",
          "procedure_failure", "hook_enter", "hook_resume"}


def read_records(directory: Path, run_id: str) -> list[dict]:
    records = []
    for component in ("CU", "DU"):
        path = directory / f"{component}-state.jsonl"
        if not path.is_file():
            raise ValueError(f"Missing {component} native state export")
        previous = 0
        process = None
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            try:
                record = json.loads(line)
                if not isinstance(record, dict) or record.get("schema") != SCHEMA:
                    raise ValueError("unknown state schema")
                if record.get("run_id") != run_id or record.get("component") != component:
                    raise ValueError("foreign run/component")
                epoch = record.get("process_epoch")
                if not isinstance(epoch, str) or not epoch or (process and epoch != process):
                    raise ValueError("missing or changed process epoch")
                process = epoch
                for key in ("sequence", "timestamp_ns", "monotonic_ns", "context_epoch", "local_ue_id",
                            "cu_ue_id", "du_ue_id", "du_rrc_state", "outcome", "delay_ms"):
                    if type(record.get(key)) is not int:
                        raise ValueError(f"invalid integer {key}")
                if record["sequence"] != previous + 1 or min(record["timestamp_ns"], record["monotonic_ns"]) <= 0:
                    raise ValueError("sequence gap or invalid clock")
                previous = record["sequence"]
                if record.get("event") not in EVENTS or record.get("procedure") not in PROCEDURES | {""}:
                    raise ValueError("unknown event/procedure")
                for key in ("context_present", "marked_for_release"):
                    if type(record.get(key)) is not bool:
                        raise ValueError(f"invalid boolean {key}")
                if record["context_epoch"] < 0 or not 0 <= record["delay_ms"] <= 2000:
                    raise ValueError("invalid epoch/delay")
                if record["context_present"] and (record["context_epoch"] == 0 or record["local_ue_id"] < 0):
                    raise ValueError("state snapshot lacks a lifecycle epoch")
                if record["event"] == "context_created" and not record["context_present"]:
                    raise ValueError("creation snapshot is absent")
                if record["event"] == "context_deleted" and record["context_present"]:
                    raise ValueError("deletion snapshot is present")
                if record["outcome"] not in {-1, 0, 1} or (record["event"] == "procedure_success" and record["outcome"] != 1):
                    raise ValueError("invalid procedure outcome")
                if record["du_rrc_state"] not in ({-1} if component == "CU" else {-1, 0, 1, 2}):
                    raise ValueError("invalid component state")
                records.append(record)
            except (ValueError, TypeError) as error:
                raise ValueError(f"{path.name}:{number}: {error}") from error
        if previous == 0:
            raise ValueError(f"Empty {component} state export")
    return records


def analyze(directory: Path, run_id: str) -> dict:
    report = {"schema": SCHEMA, "run_id": run_id, "white_box_available": False,
              "scope": "F1 context lifecycle, release flag, DU RRC configuration state",
              "attack_outcome": "inconclusive", "errors": [], "correlated_procedures": [], "hooks": []}
    try:
        records = read_records(directory, run_id)
    except (OSError, ValueError) as error:
        report["errors"].append(str(error))
        return report
    report["record_counts"] = dict(Counter(r["component"] for r in records))
    report["event_counts"] = dict(Counter(r["event"] for r in records))
    groups = defaultdict(list)
    active = {}
    seen_lifecycles = set()
    identities = defaultdict(set)
    pending_hooks = {}
    last_clock = {}
    for r in records:
        component, epoch = r["component"], r["context_epoch"]
        lifecycle = (component, r["process_epoch"], epoch)
        clock_key = (component, r["process_epoch"])
        if r["monotonic_ns"] < last_clock.get(clock_key, 0):
            report["errors"].append("Nonmonotonic native clock")
        last_clock[clock_key] = r["monotonic_ns"]
        if r["event"] == "context_created":
            if lifecycle in seen_lifecycles or (component, r["local_ue_id"]) in active.values():
                report["errors"].append("Duplicate context creation")
            seen_lifecycles.add(lifecycle)
            active[lifecycle] = (component, r["local_ue_id"])
        elif epoch and lifecycle not in active:
            report["errors"].append("Snapshot outside recorded lifecycle")
        elif epoch and active[lifecycle] != (component, r["local_ue_id"]):
            report["errors"].append("Local UE identity changed within lifecycle")
        if r["event"] == "context_deleted":
            if r["context_present"]:
                report["errors"].append("Deletion snapshot still present")
            active.pop(lifecycle, None)
        # Invalid F1 identifiers may be exported as unsigned UINT32_MAX.
        pair = (r["cu_ue_id"], r["du_ue_id"])
        valid_pair = all(0 <= value < 2**32 - 1 for value in pair)
        if valid_pair and epoch:
            identities[(component, pair)].add((r["process_epoch"], epoch))
        if valid_pair and r["event"].startswith("procedure_"):
            groups[(*pair, r["procedure"])].append(r)
        if r["event"] == "hook_enter":
            key = (*lifecycle, r["procedure"])
            if key in pending_hooks:
                report["errors"].append("Overlapping hooks cannot be correlated")
            pending_hooks[key] = r
        elif r["event"] == "hook_resume":
            start = pending_hooks.pop((*lifecycle, r["procedure"]), None)
            if start is None or start["delay_ms"] != r["delay_ms"]:
                report["errors"].append("Unmatched hook resume")
            else:
                report["hooks"].append({"component": component, "procedure": r["procedure"],
                    "context_epoch": epoch, "delay_ms": r["delay_ms"],
                    "elapsed_ns": r["monotonic_ns"] - start["monotonic_ns"]})
    report["unfinished_hooks"] = len(pending_hooks)
    report["ambiguous_identities"] = sum(len(values) != 1 for values in identities.values())
    report["unpaired_procedure_groups"] = 0
    for (cu_id, du_id, procedure), group in sorted(groups.items()):
        if any(len(identities[(component, (cu_id, du_id))]) != 1 for component in ("CU", "DU")):
            report["unpaired_procedure_groups"] += 1
            continue
        phases = {(component, event): sorted((r for r in group if r["component"] == component and r["event"] == event),
                                             key=lambda r: r["monotonic_ns"])
                  for component, event in (("CU", "procedure_send"), ("DU", "procedure_begin"),
                                           ("DU", "procedure_success"), ("CU", "procedure_success"))}
        lengths = {len(events) for events in phases.values()}
        if any(r["event"] == "procedure_failure" for r in group) or len(lengths) != 1 or 0 in lengths:
            report["unpaired_procedure_groups"] += 1
            continue
        chains = list(zip(*phases.values()))
        # Only a serialized, complete native send/begin/response/result chain is joined.
        previous_end = -1
        valid = True
        for chain in chains:
            times = [r["monotonic_ns"] for r in chain]
            if times != sorted(times) or times[0] <= previous_end:
                valid = False
            previous_end = times[-1]
        if not valid:
            report["unpaired_procedure_groups"] += 1
            continue
        for ordinal, chain in enumerate(chains, 1):
            report["correlated_procedures"].append({"cu_ue_id": cu_id, "du_ue_id": du_id,
                "procedure": procedure, "ordinal": ordinal, "cu_context_epoch": chain[0]["context_epoch"],
                "du_context_epoch": chain[1]["context_epoch"],
                "elapsed_ns": chain[-1]["monotonic_ns"] - chain[0]["monotonic_ns"]})
    report["white_box_available"] = (bool(report["correlated_procedures"]) and not report["errors"]
                                    and not report["ambiguous_identities"] and not report["unfinished_hooks"])
    report["clock_assumption"] = "Native ordering requires a shared kernel and equal time-namespace offsets; the context check verifies them"
    report["limitation"] = "Procedure coverage only; use the inventory check for settled F1 presence. No bearer/security verdict."
    return report
