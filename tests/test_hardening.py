"""Tests for hardened input validation and edge-case handling."""
from __future__ import annotations
import json
import pytest

from readiness_rms.core import (
    c_rating,
    compute_rating,
    scan,
    UnitInputs,
    InputValidationError,
    _validate_unit_data,
)

# ---------------------------------------------------------------------------
# c_rating edge cases
# ---------------------------------------------------------------------------

def test_c_rating_boundary_exact_85():
    assert c_rating(85) == "C1"

def test_c_rating_boundary_exact_70():
    assert c_rating(70) == "C2"

def test_c_rating_boundary_exact_60():
    assert c_rating(60) == "C3"

def test_c_rating_zero():
    assert c_rating(0) == "C4"

def test_c_rating_non_numeric_returns_c4():
    # Non-numeric input (e.g. None from a corrupt record) should not raise
    assert c_rating(None) == "C4"  # type: ignore[arg-type]

def test_c_rating_nan_returns_c4():
    import math
    assert c_rating(math.nan) == "C4"


# ---------------------------------------------------------------------------
# _validate_unit_data
# ---------------------------------------------------------------------------

VALID_DATA = {
    "unit_id": "TEST-01",
    "personnel_assigned": 700,
    "personnel_required": 700,
    "personnel_deployable": 650,
    "equipment_on_hand_pct": 90.0,
    "equipment_mission_capable_pct": 85.0,
    "training_current_pct": 80.0,
    "inspection_pass_pct": 88.0,
}


def test_validate_accepts_valid_data():
    result = _validate_unit_data(VALID_DATA, source="test")
    assert result["unit_id"] == "TEST-01"


def test_validate_rejects_non_dict():
    with pytest.raises(InputValidationError, match="Expected a JSON object"):
        _validate_unit_data(["not", "a", "dict"])


def test_validate_rejects_missing_field():
    data = dict(VALID_DATA)
    del data["unit_id"]
    with pytest.raises(InputValidationError, match="Missing required field"):
        _validate_unit_data(data, source="test.json")


def test_validate_rejects_wrong_type():
    data = dict(VALID_DATA, unit_id=42)  # unit_id must be str
    with pytest.raises(InputValidationError, match="unit_id"):
        _validate_unit_data(data)


def test_validate_rejects_pct_above_100():
    data = dict(VALID_DATA, equipment_on_hand_pct=110.0)
    with pytest.raises(InputValidationError, match="equipment_on_hand_pct"):
        _validate_unit_data(data)


def test_validate_rejects_pct_below_0():
    data = dict(VALID_DATA, training_current_pct=-5.0)
    with pytest.raises(InputValidationError, match="training_current_pct"):
        _validate_unit_data(data)


def test_validate_rejects_negative_personnel():
    data = dict(VALID_DATA, personnel_assigned=-1)
    with pytest.raises(InputValidationError, match="personnel_assigned"):
        _validate_unit_data(data)


# ---------------------------------------------------------------------------
# scan() edge cases
# ---------------------------------------------------------------------------

def test_scan_empty_directory(tmp_path):
    """Directory with no JSON files returns an empty ScanResult (no crash)."""
    result = scan(str(tmp_path))
    assert result.items_scanned == 0
    assert result.total_findings() == 0


def test_scan_single_file_path(tmp_path):
    """scan() accepts a single JSON file path, not just a directory."""
    f = tmp_path / "unit.json"
    f.write_text(json.dumps(VALID_DATA), encoding="utf-8")
    result = scan(str(f))
    assert result.items_scanned == 1
    assert result.total_findings() == 1


def test_scan_missing_path_exits_2(tmp_path):
    """Passing a non-existent path should call sys.exit(2)."""
    with pytest.raises(SystemExit) as exc_info:
        scan(str(tmp_path / "does_not_exist"))
    assert exc_info.value.code == 2


def test_scan_malformed_json_exits_2(tmp_path):
    """A file with invalid JSON should call sys.exit(2), not raise a traceback."""
    bad = tmp_path / "bad.json"
    bad.write_text("{this is not json}", encoding="utf-8")
    with pytest.raises(SystemExit) as exc_info:
        scan(str(bad))
    assert exc_info.value.code == 2


def test_scan_missing_required_field_exits_2(tmp_path):
    """JSON missing a required field exits with code 2."""
    data = dict(VALID_DATA)
    del data["inspection_pass_pct"]
    bad = tmp_path / "incomplete.json"
    bad.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(SystemExit) as exc_info:
        scan(str(bad))
    assert exc_info.value.code == 2


def test_scan_pct_out_of_range_exits_2(tmp_path):
    """JSON with a percentage > 100 exits with code 2."""
    data = dict(VALID_DATA, equipment_mission_capable_pct=150.0)
    bad = tmp_path / "bad_pct.json"
    bad.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(SystemExit) as exc_info:
        scan(str(bad))
    assert exc_info.value.code == 2


def test_scan_extra_keys_are_ignored(tmp_path):
    """Extra keys in the JSON should not cause a crash."""
    data = dict(VALID_DATA, extra_field="ignored", another_field=999)
    f = tmp_path / "unit_extra.json"
    f.write_text(json.dumps(data), encoding="utf-8")
    result = scan(str(f))
    assert result.total_findings() == 1


# ---------------------------------------------------------------------------
# compute_rating edge cases
# ---------------------------------------------------------------------------

def test_compute_rating_zero_required_personnel():
    """personnel_required=0 must not cause ZeroDivisionError."""
    u = UnitInputs("GHOST", 0, 0, 0, 90.0, 85.0, 80.0, 88.0)
    result = compute_rating(u)
    assert result["overall"] in ("C1", "C2", "C3", "C4")


def test_compute_rating_overstrenght_unit():
    """Over-strength unit (assigned > required) should not exceed 100% fill."""
    u = UnitInputs("OVER", 900, 700, 850, 95.0, 90.0, 92.0, 95.0)
    result = compute_rating(u)
    assert result["personnel_fill_pct"] <= 100.0
    assert result["personnel_deployable_pct"] <= 100.0
    assert result["overall"] == "C1"
