from types import SimpleNamespace

from faceguard.track_health import evaluate_tracking_health


CFG = {
    "max_center_jump_px": 80,
    "max_area_ratio": 2.5,
    "min_area_ratio": 0.4,
    "max_oob_ratio": 0.2,
    "max_missed_detects_before_redetect": 3,
}


def _person(**kwargs):
    base = dict(
        tracker=object(),
        bbox=(100, 100, 50, 50),
        last_detect_area=2500.0,
        _prev_center=(125.0, 125.0),
        missed_detect_count=0,
    )
    base.update(kwargs)
    return SimpleNamespace(**base)


def test_health_ok():
    ok, reason = evaluate_tracking_health(_person(), 1280, 720, CFG)
    assert ok is True
    assert reason == "ok"


def test_health_tracker_none():
    ok, reason = evaluate_tracking_health(_person(tracker=None), 1280, 720, CFG)
    assert ok is False
    assert reason == "tracker_none"


def test_health_area_jump():
    ok, reason = evaluate_tracking_health(_person(bbox=(100, 100, 200, 200)), 1280, 720, CFG)
    assert ok is False
    assert reason == "bbox_area_jump"
