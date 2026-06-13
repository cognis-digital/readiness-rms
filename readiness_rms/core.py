"""readiness-rms — compute C-rating (C1-C4) from public DoD inputs."""
from __future__ import annotations
import json
from pathlib import Path
from dataclasses import dataclass
from cognis_mil import ScanResult, Finding, Severity

# C-rating thresholds (public DoD doctrine: AR 220-1, OPNAVINST 3501.226, etc.)
# C1: ≥85%  C2: 70-84%  C3: 60-69%  C4: <60% (or "N" for not-ready)
def c_rating(percent: float) -> str:
    if percent >= 85: return "C1"
    if percent >= 70: return "C2"
    if percent >= 60: return "C3"
    return "C4"

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
    personnel_fill = (u.personnel_assigned / u.personnel_required) * 100 if u.personnel_required else 100
    personnel_avail = (u.personnel_deployable / u.personnel_required) * 100 if u.personnel_required else 100
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
    files = list(p.glob("*.json")) if p.is_dir() else [p]
    r.items_scanned = len(files)
    for f in files:
        if not f.is_file(): continue
        data = json.loads(f.read_text())
        u = UnitInputs(**data)
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
    r.finalize(); return r
