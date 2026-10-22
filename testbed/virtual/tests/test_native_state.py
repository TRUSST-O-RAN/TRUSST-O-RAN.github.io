"""Native lifecycle/procedure evidence must remain unambiguous and fail closed."""
import json
from unittest.mock import patch

import pytest

from testbed.virtual.instrumentation import instrument
from testbed.virtual.instrumentation.state import analyze
from testbed.virtual.instrumentation.runner import validate_plan


def record(component, sequence, timestamp, event, procedure="", **fields):
    return {"schema": "trusst.f1-state.v1", "run_id": "run-1", "component": component,
            "process_epoch": component+"-boot", "sequence": sequence, "timestamp_ns": timestamp+1000,
            "monotonic_ns": timestamp, "context_epoch": 1, "local_ue_id": 0,
            "cu_ue_id": 3, "du_ue_id": 7, "context_present": True, "marked_for_release": False,
            "du_rrc_state": -1 if component == "CU" else 1, "event": event,
            "procedure": procedure, "outcome": -1, "delay_ms": 0, **fields}


def native_trace():
    return [record("CU", 1, 1, "context_created"), record("CU", 2, 3, "procedure_send", "SETUP"),
            record("CU", 3, 9, "procedure_success", "SETUP", outcome=1),
            record("DU", 1, 2, "context_created"), record("DU", 2, 4, "procedure_begin", "SETUP"),
            record("DU", 3, 5, "hook_enter", "SETUP"), record("DU", 4, 6, "hook_resume", "SETUP"),
            record("DU", 5, 8, "procedure_success", "SETUP", outcome=1)]


def write_trace(tmp_path, records):
    for component in ("CU", "DU"):
        (tmp_path/f"{component}-state.jsonl").write_text(
            "".join(json.dumps(r)+"\n" for r in records if r["component"] == component), encoding="utf-8")
    return analyze(tmp_path, "run-1")


def test_complete_native_chain_is_coverage_only(tmp_path):
    result = write_trace(tmp_path, native_trace())
    assert result["white_box_available"]
    assert result["attack_outcome"] == "inconclusive"
    assert result["correlated_procedures"] == [{"cu_ue_id": 3, "du_ue_id": 7, "procedure": "SETUP",
        "ordinal": 1, "cu_context_epoch": 1, "du_context_epoch": 1, "elapsed_ns": 6}]
    assert result["hooks"][0]["elapsed_ns"] == 1


@pytest.mark.parametrize("field,value", [("run_id", "foreign"), ("process_epoch", "other-boot"),
    ("sequence", 4), ("sequence", True), ("context_epoch", 0), ("context_present", "true"),
    ("monotonic_ns", -1), ("schema", "unknown"), ("du_rrc_state", 9), ("delay_ms", 2001)])
def test_corrupt_or_foreign_state_is_rejected(tmp_path, field, value):
    trace = native_trace()
    trace[1][field] = value
    result = write_trace(tmp_path, trace)
    assert not result["white_box_available"]
    assert result["errors"]


def test_unpaired_response_is_not_a_transaction(tmp_path):
    trace = native_trace()
    trace[2].update(event="procedure_failure", outcome=0)
    result = write_trace(tmp_path, trace)
    assert not result["white_box_available"]
    assert result["unpaired_procedure_groups"] == 1


def test_reused_native_ids_are_not_joined_across_epochs(tmp_path):
    trace = native_trace()
    trace.extend([record("DU", 6, 10, "context_deleted", context_present=False),
                  record("DU", 7, 11, "context_created", context_epoch=2)])
    result = write_trace(tmp_path, trace)
    assert not result["white_box_available"]
    assert result["ambiguous_identities"] == 1


def test_protocol_complete_after_deletion_never_dereferences_a_context(tmp_path):
    trace = native_trace()
    trace.extend([record("DU", 6, 10, "context_deleted", context_present=False),
                  record("DU", 7, 11, "procedure_success", "RELEASE", outcome=1, context_present=False,
                         local_ue_id=-1, context_epoch=0)])
    result = write_trace(tmp_path, trace)
    assert not result["errors"]
    assert result["unpaired_procedure_groups"] == 1


def test_same_epoch_cannot_be_recycled(tmp_path):
    trace = native_trace()
    trace.extend([record("DU", 6, 10, "context_deleted", context_present=False),
                  record("DU", 7, 11, "context_created")])
    assert not write_trace(tmp_path, trace)["white_box_available"]


def test_missing_or_partial_native_trace_is_not_white_box(tmp_path):
    assert not analyze(tmp_path, "run-1")["white_box_available"]
    write_trace(tmp_path, native_trace())
    with (tmp_path/"DU-state.jsonl").open("a") as stream:
        stream.write('{"schema":')
    assert not analyze(tmp_path, "run-1")["white_box_available"]


@pytest.mark.parametrize("value", [-1, 2001, True, 1.5, "100"])
def test_hook_bounds_checked_before_starting_docker(value):
    with pytest.raises(ValueError):
        validate_plan({"virtual": {"action": "observe", "instrumentation": {"setup_ms": value}}})


def test_unknown_hook_and_wrong_image_fail_closed():
    with pytest.raises(ValueError):
        instrument.validate({"drop_packets": 1})
    with patch.object(instrument.lab, "run") as command:
        command.return_value.stdout = json.dumps([{"Id": "old-image", "Config": {"Labels": {}}}])
        with pytest.raises(ValueError, match="does not match"):
            instrument.verify_image()


def test_clock_order_cannot_manufacture_a_native_chain(tmp_path):
    trace = native_trace()
    trace[2]["monotonic_ns"] = 7  # CU result predates DU response.
    result = write_trace(tmp_path, trace)
    assert not result["white_box_available"]
    assert result["unpaired_procedure_groups"] == 1


def test_completed_procedure_does_not_hide_an_unfinished_hook(tmp_path):
    trace = native_trace()
    trace.append(record("DU", 6, 10, "hook_enter", "RELEASE", delay_ms=100))
    result = write_trace(tmp_path, trace)
    assert result["correlated_procedures"]
    assert result["unfinished_hooks"] == 1
    assert not result["white_box_available"]


@pytest.mark.parametrize("value", [-1, 0, 4, 121, True, 8.5])
def test_inactivity_bounds(value):
    with pytest.raises(ValueError):
        instrument.validate({"inactivity_s": value})


def test_idle_release_requires_explicit_native_inactivity_configuration():
    with pytest.raises(ValueError, match="inactivity_s"):
        validate_plan({"virtual": {"action": "ue_idle_release"}})


def test_armed_hook_files_are_portable_and_startup_delays_are_disabled(tmp_path):
    settings = {"release_ms": 1500, "arm_after_baseline": True}
    env = instrument.environment(tmp_path, "run-1", settings)
    assert env["TRUSST_HOOK_RELEASE_MS"] == "0"
    instrument.arm_hooks(tmp_path, settings)
    assert (tmp_path/"hooks/RELEASE.ms").read_bytes() == b"1500\n"
    assert (tmp_path/"hooks/SETUP.ms").read_bytes() == b"0\n"
