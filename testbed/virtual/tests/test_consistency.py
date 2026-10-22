"""Settled-state checks reject capture faults and detect a persistent one-sided context."""
import json
from pathlib import Path

import pytest

from testbed.virtual.instrumentation.consistency import check

START, END = 2_000_000_000, 5_000_000_000


def fixture_files(directory):
    for component in ("CU", "DU"):
        events = []
        for sequence, (event, stamp, procedure) in enumerate([
            ("context_created", 1_000_000, ""),
            ("procedure_send" if component == "CU" else "procedure_begin", 2_000_000 if component == "CU" else 3_000_000, "SETUP"),
            ("procedure_success", 5_000_000 if component == "CU" else 4_000_000, "SETUP")], 1):
            events.append({"schema": "trusst.f1-state.v1", "run_id": "test", "component": component,
                "process_epoch": component+"-process", "sequence": sequence, "timestamp_ns": stamp+100,
                "monotonic_ns": stamp, "context_epoch": 1, "local_ue_id": 0, "cu_ue_id": 0, "du_ue_id": 0,
                "context_present": True, "marked_for_release": False, "du_rrc_state": -1,
                "event": event, "procedure": procedure, "outcome": 1 if event == "procedure_success" else -1,
                "delay_ms": 0})
        write(directory/f"{component}-state.jsonl", events)
        rows = [{"schema": "trusst.f1-inventory.v1", "run_id": "test", "component": component,
            "process_epoch": component+"-process", "boot_id": "boot", "clock_namespace": "time:[1]",
            "monotonic_offset_ns": 0,
            "sequence": sequence, "timestamp_ns": stamp+100, "monotonic_ns": stamp,
            "repository_epoch": 1, "association_epoch": 1,
            "contexts": [{"local_ue_id": 0, "cu_ue_id": 0, "du_ue_id": 0, "context_epoch": 1}]}
            for sequence, stamp in enumerate(range(500_000_000, 5_500_000_000, 250_000_000), 1)]
        write(directory/f"{component}-inventory.jsonl", rows)


def write(path, rows):
    path.write_text("".join(json.dumps(row)+"\n" for row in rows), encoding="utf-8")


def change(directory, filename, update):
    path = directory/filename
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    update(rows)
    write(path, rows)


def test_complete_settled_window(tmp_path):
    fixture_files(tmp_path)
    result = check(tmp_path, "test", START, END)
    assert result["outcome"] == "no_inconsistency_observed"
    assert result["paired_samples"] == 13
    assert not result["errors"]


def test_persistent_one_sided_context_is_a_candidate(tmp_path):
    fixture_files(tmp_path)
    change(tmp_path, "DU-inventory.jsonl", lambda rows: [row.update(contexts=[]) for row in rows])
    result = check(tmp_path, "test", START, END)
    assert result["outcome"] == "candidate_inconsistency"
    assert result["mismatch_duration_lower_bound_ns"] == END-START
    assert result["mismatches"][0]["cu_only"] == [(0, 0)]


def test_short_mismatch_is_not_a_confirmed_candidate(tmp_path):
    fixture_files(tmp_path)
    change(tmp_path, "DU-inventory.jsonl", lambda rows: rows[7].update(contexts=[]))
    assert check(tmp_path, "test", START, END)["outcome"] == "inconclusive"


@pytest.mark.parametrize("field,value", [("run_id", "foreign"), ("boot_id", "other-kernel"),
    ("clock_namespace", "time:[2]"), ("process_epoch", "other-process"), ("sequence", 99),
    ("association_epoch", 2), ("repository_epoch", 2), ("monotonic_ns", True), ("contexts", None)])
def test_incomplete_or_uncorrelated_capture_is_inconclusive(tmp_path, field, value):
    fixture_files(tmp_path)
    change(tmp_path, "DU-inventory.jsonl", lambda rows: rows[8].update({field: value}))
    result = check(tmp_path, "test", START, END)
    assert result["outcome"] == "inconclusive"
    assert result["errors"]


def test_missing_samples_are_not_absent_contexts(tmp_path):
    fixture_files(tmp_path)
    (tmp_path/"DU-inventory.jsonl").unlink()
    assert check(tmp_path, "test", START, END)["outcome"] == "inconclusive"


def test_clock_gap_with_unbroken_sequence_is_inconclusive(tmp_path):
    fixture_files(tmp_path)
    def gap(rows):
        rows[:] = [r for r in rows if not 2_000_000_000 < r["monotonic_ns"] < 4_000_000_000]
        for number, row in enumerate(rows, 1): row["sequence"] = number
    change(tmp_path, "DU-inventory.jsonl", gap)
    assert check(tmp_path, "test", START, END)["outcome"] == "inconclusive"


def test_pending_procedure_masks_mismatches(tmp_path):
    fixture_files(tmp_path)
    def pending(rows):
        row = dict(rows[-1], sequence=4, event="procedure_send", procedure="MODIFICATION",
                   monotonic_ns=1_500_000_000, timestamp_ns=1_500_000_100, outcome=-1)
        rows.append(row)
    change(tmp_path, "CU-state.jsonl", pending)
    change(tmp_path, "DU-inventory.jsonl", lambda rows: [row.update(contexts=[]) for row in rows])
    result = check(tmp_path, "test", START, END)
    assert result["outcome"] == "inconclusive"
    assert result["excluded_pending"] == 13


def test_unrecorded_allocation_is_inconclusive(tmp_path):
    fixture_files(tmp_path)
    change(tmp_path, "DU-inventory.jsonl", lambda rows: rows[8]["contexts"][0].update(context_epoch=2))
    assert check(tmp_path, "test", START, END)["outcome"] == "inconclusive"


def test_different_namespace_ids_with_equal_offsets_share_the_clock(tmp_path):
    fixture_files(tmp_path)
    change(tmp_path, "DU-inventory.jsonl", lambda rows: [r.update(clock_namespace="time:[2]") for r in rows])
    assert check(tmp_path, "test", START, END)["outcome"] == "no_inconsistency_observed"


def test_different_namespace_offsets_are_not_compared(tmp_path):
    fixture_files(tmp_path)
    change(tmp_path, "DU-inventory.jsonl", lambda rows: [r.update(monotonic_offset_ns=100) for r in rows])
    assert check(tmp_path, "test", START, END)["outcome"] == "inconclusive"
