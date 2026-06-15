"""readiness-rms — compute C-rating (C1-C4) from public DoD inputs."""
from __future__ import annotations
import json
import sys
from pathlib import Path
from dataclasses import dataclass
from cognis_mil import ScanResult, Finding, Severity

# C-rating thresholds (public DoD doctrine: AR 220-1, OPNAVINST 3501.226, etc.)
# C1: ≥85%  C2: 70-84%  C3: 60-69%  C4: <60% (or "N" for not-ready)
def c_rating(percent: float) -> str:
    if not isinstance(percent, (int, float)) or percent != percent:  # NaN guard
        return "C4"
    if percent >= 85:
        return "C1"
    if percent >= 70:
        return "C2"
    if percent >= 60:
        return "C3"
    return "C4"

# Required fields and their expected types for UnitInputs JSON
_REQUIRED_FIELDS: dict[str, type] = {
    "unit_id": str,
    "personnel_assigned": (int, float),
    "personnel_required": (int, float),
    "personnel_deployable": (int, float),
    "equipment_on_hand_pct": (int, float),
    "equipment_mission_capable_pct": (int, float),
    "training_current_pct": (int, float),
    "inspection_pass_pct": (int, float),
}

_PCT_FIELDS = {
    "equipment_on_hand_pct",
    "equipment_mission_capable_pct",
    "training_current_pct",
    "inspection_pass_pct",
}


class InputValidationError(ValueError):
    """Raised when a unit JSON file fails validation."""


def _validate_unit_data(data: object, source: str = "") -> dict:
    """Validate raw parsed JSON for a unit record.

    Returns the validated dict on success; raises InputValidationError with a
    descriptive message on failure.
    """
    loc = f" in {source}" if source else ""
    if not isinstance(data, dict):
        raise InputValidationError(
            f"Expected a JSON object{loc}, got {type(data).__name__}"
        )
    missing = [k for k in _REQUIRED_FIELDS if k not in data]
    if missing:
        raise InputValidationError(
            f"Missing required field(s){loc}: {', '.join(missing)}"
        )
    for field, expected in _REQUIRED_FIELDS.items():
        val = data[field]
        if not isinstance(val, expected):
            raise InputValidationError(
                f"Field '{field}'{loc} must be {expected}, got {type(val).__name__}"
            )
    for pf in _PCT_FIELDS:
        val = data[pf]
        if val < 0 or val > 100:
            raise InputValidationError(
                f"Field '{pf}'{loc} must be 0–100, got {val}"
            )
    for count_field in (
        "personnel_assigned", "personnel_required", "personnel_deployable"
    ):
        if data[count_field] < 0:
            raise InputValidationError(
                f"Field '{count_field}'{loc} must be >= 0, got {data[count_field]}"
            )
    return data


@dataclass
class UnitInputs:
    unit_id: str
    personnel_assigned: int
    personnel_required: int
    personnel_deployable: int        # MRC4 in army-speak
    equipment_on_hand_pct: float
    equipment_mission_capable_pct: float
    training_current_pct: float      # percent w/ training currency
    inspection_pass_pct: float

def compute_rating(u: UnitInputs) -> dict:
    req = u.personnel_required
    personnel_fill = (u.personnel_assigned / req) * 100 if req else 100
    personnel_avail = (u.personnel_deployable / req) * 100 if req else 100
    # Cap derived percentages at 100 (over-strength units still rate C1)
    personnel_fill = min(personnel_fill, 100.0)
    personnel_avail = min(personnel_avail, 100.0)
    # Overall C-rating is the WORST of the sub-ratings
    sub = {
        "P_fill":           c_rating(personnel_fill),
        "P_deployable":     c_rating(personnel_avail),
        "E_on_hand":        c_rating(u.equipment_on_hand_pct),
        "E_mission_capable":c_rating(u.equipment_mission_capable_pct),
        "T_current":        c_rating(u.training_current_pct),
        "Inspection":       c_rating(u.inspection_pass_pct),
    }
    order = ["C1","C2","C3","C4"]
    worst = max(sub.values(), key=lambda x: order.index(x))
    return {
        "unit_id": u.unit_id, "overall": worst, "subratings": sub,
        "personnel_fill_pct": round(personnel_fill,1),
        "personnel_deployable_pct": round(personnel_avail,1),
    }

def scan(target=".", **opts):
    r = ScanResult(tool_name="readiness-rms", tool_version="0.1.0")
    p = Path(target)
    if not p.exists():
        print(f"error: target path does not exist: {target}", file=sys.stderr)
        sys.exit(2)
    files = list(p.glob("*.json")) if p.is_dir() else [p]
    if not files:
        r.finalize()
        return r
    r.items_scanned = len(files)
    for f in files:
        if not f.is_file():
            continue
        # Parse JSON with a clear error on malformed input
        try:
            raw = f.read_text(encoding="utf-8")
        except OSError as exc:
            print(f"error: cannot read {f}: {exc}", file=sys.stderr)
            sys.exit(2)
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            print(f"error: {f} is not valid JSON: {exc}", file=sys.stderr)
            sys.exit(2)
        # Validate structure and field ranges
        try:
            _validate_unit_data(data, source=str(f))
        except InputValidationError as exc:
            print(f"error: {exc}", file=sys.stderr)
            sys.exit(2)
        # Build dataclass — only known fields (ignore any extra keys gracefully)
        known = {k for k in _REQUIRED_FIELDS}
        u = UnitInputs(**{k: v for k, v in data.items() if k in known})
        rating = compute_rating(u)
        if rating["overall"] == "C4":
            r.add(Finding(f"RR-C4-{u.unit_id}", Severity.VERY_HIGH,
                          f"{u.unit_id}: C4 (not ready)",
                          location=str(f),
                          description=f"Subratings: {rating['subratings']}",
                          remediation="Drill into subratings; brief commander."))
        elif rating["overall"] == "C3":
            r.add(Finding(f"RR-C3-{u.unit_id}", Severity.HIGH,
                          f"{u.unit_id}: C3 (degraded)",
                          location=str(f),
                          description=f"Subratings: {rating['subratings']}"))
        else:
            r.add(Finding(f"RR-OK-{u.unit_id}", Severity.VERY_LOW,
                          f"{u.unit_id}: {rating['overall']}", location=str(f)))
    r.finalize()
    return r
