from pathlib import Path
from readiness_rms.core import UnitInputs, compute_rating, c_rating, scan
D = Path(__file__).parent.parent / "demos"
def test_c_rating_thresholds():
    assert c_rating(90) == "C1"
    assert c_rating(75) == "C2"
    assert c_rating(65) == "C3"
    assert c_rating(50) == "C4"
def test_compute_strong():
    u = UnitInputs("X",700,700,690,95,90,92,95)
    r = compute_rating(u)
    assert r["overall"] == "C1"
def test_compute_weak():
    u = UnitInputs("X",400,700,300,55,50,40,60)
    r = compute_rating(u)
    assert r["overall"] == "C4"
def test_scan():
    r = scan(str(D))
    ids = {f.id for f in r.findings}
    # Unit 5678 should be C4
    assert any("C4" in i for i in ids)
