"""Compare fresh CU/DU F1 context inventories after control procedures settle."""
from __future__ import annotations

import json
from pathlib import Path

from .state import analyze, read_records


def read_inventories(directory: Path, run_id: str) -> dict[str, list[dict]]:
    result = {}
    for component in ("CU", "DU"):
        rows = []
        previous = 0
        for line in (directory / f"{component}-inventory.jsonl").read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            if not isinstance(row, dict) or row.get("schema") != "trusst.f1-inventory.v1":
                raise ValueError("Unknown inventory schema")
            if row.get("run_id") != run_id or row.get("component") != component:
                raise ValueError("Foreign inventory run or component")
            for key in ("sequence", "timestamp_ns", "monotonic_ns", "repository_epoch", "association_epoch"):
                if type(row.get(key)) is not int or row[key] < 0:
                    raise ValueError(f"Invalid inventory {key}")
            if type(row.get("monotonic_offset_ns")) is not int or row["repository_epoch"] == 0:
                raise ValueError("Missing clock offset or repository epoch")
            if row["sequence"] != previous + 1 or row["monotonic_ns"] <= 0:
                raise ValueError("Inventory sequence gap or invalid clock")
            previous = row["sequence"]
            for key in ("process_epoch", "boot_id", "clock_namespace"):
                if not isinstance(row.get(key), str) or not row[key]:
                    raise ValueError(f"Missing inventory {key}")
            if not isinstance(row.get("contexts"), list):
                raise ValueError("Incomplete inventory")
            local_ids = set()
            for context in row["contexts"]:
                if not isinstance(context, dict):
                    raise ValueError("Invalid inventory entry")
                for key in ("local_ue_id", "cu_ue_id", "du_ue_id", "context_epoch"):
                    if type(context.get(key)) is not int:
                        raise ValueError(f"Invalid context {key}")
                if context["local_ue_id"] < 0 or context["context_epoch"] <= 0 or context["local_ue_id"] in local_ids:
                    raise ValueError("Missing or duplicate allocation identity")
                local_ids.add(context["local_ue_id"])
            if rows and row["monotonic_ns"] <= rows[-1]["monotonic_ns"]:
                raise ValueError("Nonmonotonic inventory clock")
            # DU sampling starts before its first association is established.
            if row["association_epoch"] == 0:
                if row["contexts"]:
                    raise ValueError("Contexts without an association")
                continue
            rows.append(row)
        if not rows:
            raise ValueError(f"Missing {component} inventory coverage")
        for key in ("process_epoch", "boot_id", "clock_namespace", "monotonic_offset_ns", "repository_epoch", "association_epoch"):
            if len({row[key] for row in rows}) != 1:
                raise ValueError(f"Changed {component} {key}; association changes require separate runs")
        result[component] = rows
    for key in ("boot_id", "monotonic_offset_ns"):
        if result["CU"][0][key] != result["DU"][0][key]:
            raise ValueError("CU/DU inventories do not share a Linux clock domain")
    return result


def check(directory: Path, run_id: str, start_ns: int, end_ns: int, *, settling_ms: int = 1000,
          max_skew_ms: int = 200, max_gap_ms: int = 750, persistence_ms: int = 1000) -> dict:
    report = {"outcome": "inconclusive", "scope": "sampled F1 context presence", "run_id": run_id,
              "window": {"start_ns": start_ns, "end_ns": end_ns}, "errors": [],
              "paired_samples": 0, "excluded_pending": 0, "mismatches": [],
              "settling_ms": settling_ms, "max_skew_ms": max_skew_ms,
              "max_gap_ms": max_gap_ms, "persistence_ms": persistence_ms}
    try:
        for value in (start_ns, end_ns, settling_ms, max_skew_ms, max_gap_ms, persistence_ms):
            if type(value) is not int or value < 0:
                raise ValueError("Window and timing bounds must be nonnegative integers")
        if end_ns - start_ns < 1_500_000_000 or min(max_skew_ms, max_gap_ms, persistence_ms) <= 0:
            raise ValueError("Need a measurement window of at least 1.5 seconds and positive sampling bounds")
        coverage = analyze(directory, run_id)
        if not coverage["white_box_available"]:
            raise ValueError("Native lifecycle/procedure coverage unavailable")
        events = read_records(directory, run_id)
        inventories = read_inventories(directory, run_id)
        known = {(r["component"], r["process_epoch"], r["context_epoch"], r["local_ue_id"])
                 for r in events if r["event"] == "context_created"}
        for component, rows in inventories.items():
            process = next(r["process_epoch"] for r in events if r["component"] == component)
            if rows[0]["process_epoch"] != process:
                raise ValueError("Lifecycle and inventory process epochs differ")
            for row in rows:
                for context in row["contexts"]:
                    if (component, process, context["context_epoch"], context["local_ue_id"]) not in known:
                        raise ValueError("Inventory allocation has no native creation record")
        pending = {}
        excluded = []
        for row in sorted(events, key=lambda r: (r["monotonic_ns"], r["component"], r["sequence"])):
            key = (row["component"], row["cu_ue_id"], row["procedure"])
            if row["event"] in {"procedure_send", "procedure_begin"}:
                if key in pending:
                    raise ValueError("Overlapping same-kind procedures cannot be bounded")
                pending[key] = row["monotonic_ns"]
            elif row["event"] in {"procedure_success", "procedure_failure"}:
                begun = pending.pop(key, None)
                if begun is not None:
                    excluded.append((begun, row["monotonic_ns"] + settling_ms * 1_000_000))
        excluded.extend((begun, 2**63 - 1) for begun in pending.values())
        cu = [r for r in inventories["CU"] if start_ns <= r["monotonic_ns"] <= end_ns]
        du = [r for r in inventories["DU"] if start_ns <= r["monotonic_ns"] <= end_ns]
        pairs = []
        i = j = 0
        while i < len(cu) and j < len(du):
            left, right = cu[i], du[j]
            delta = left["monotonic_ns"] - right["monotonic_ns"]
            if abs(delta) > max_skew_ms * 1_000_000:
                if delta < 0: i += 1
                else: j += 1
                continue
            i += 1; j += 1
            low, high = sorted((left["monotonic_ns"], right["monotonic_ns"]))
            if any(low <= finish and high >= begin for begin, finish in excluded):
                report["excluded_pending"] += 1
                continue
            sets = []
            for row in (left, right):
                identifiers = [(c["cu_ue_id"], c["du_ue_id"]) for c in row["contexts"]]
                if any(not all(0 <= v < 2**32 - 1 for v in pair) for pair in identifiers) or len(set(identifiers)) != len(identifiers):
                    raise ValueError("Unbound or duplicate F1 identifiers in the measurement window")
                sets.append(set(identifiers))
            difference = {"cu_only": sorted(sets[0] - sets[1]), "du_only": sorted(sets[1] - sets[0])}
            pairs.append((high, difference))
            if any(difference.values()):
                report["mismatches"].append({"monotonic_ns": high, **difference})
        report["paired_samples"] = len(pairs)
        report["inventory_counts"] = {c: len(rows) for c, rows in inventories.items()}
        if len(pairs) < 3:
            raise ValueError("Too few paired settled samples")
        times = [t for t, _ in pairs]
        gaps = [times[0] - start_ns, end_ns - times[-1], *[b-a for a,b in zip(times, times[1:])]]
        if max(gaps) > max_gap_ms * 1_000_000:
            raise ValueError("Inventory coverage has a gap beyond the sampling bound")
        report["observed_span_ns"] = times[-1] - times[0]
        report["maximum_gap_ns"] = max(gaps)
        if not report["mismatches"]:
            report["outcome"] = "no_inconsistency_observed"
        else:
            previous = None
            first = 0
            longest = 0
            for timestamp, difference in pairs:
                if any(difference.values()):
                    if difference != previous:
                        first = timestamp
                    longest = max(longest, timestamp-first)
                    previous = difference
                else:
                    previous = None
            report["mismatch_duration_lower_bound_ns"] = longest
            report["outcome"] = "candidate_inconsistency" if longest >= persistence_ms*1_000_000 else "inconclusive"
        report["limitation"] = "Sampled F1 presence only; bearer, RLC/MAC and security consistency are not tested"
    except (OSError, ValueError, KeyError, TypeError) as error:
        report["errors"].append(str(error))
    return report
