from faceguard.fsm import FSMConfig, PersonFSM, FSMState


def _cfg() -> FSMConfig:
    return FSMConfig.from_dict(
        {
            "enabled": True,
            "min_dwell_ms": {"calm": 0, "suspect": 3000, "threat": 5000},
            "thresholds": {
                "suspect_enter": {"threat_mean_min": 20, "neg_ratio_min": 0.20, "motion_p95_min": 0.10},
                "suspect_exit": {"threat_mean_max": 12, "neg_ratio_max": 0.12, "motion_p95_max": 0.08},
                "threat_enter": {"threat_p95_min": 70, "threat_mean_min": 40, "neg_ratio_min": 0.35, "motion_p95_min": 0.15},
                "threat_exit": {"threat_p95_max": 55, "threat_mean_max": 28, "neg_ratio_max": 0.25, "motion_p95_max": 0.12},
            },
            "quality_gate": {"min_valid_ratio": 0.30, "min_face_presence_ratio": 0.30},
            "no_face_timeout_ms": 1500,
            "low_quality_timeout_ms": 2000,
        },
        fallback_min_valid_ratio=0.3,
    )


def test_hysteresis_and_min_dwell():
    fsm = PersonFSM(_cfg())
    calm = {"threat_mean": 5, "threat_p95": 15, "neg_ratio": 0.05, "motion_p95": 0.03, "valid_ratio": 0.9, "face_presence_ratio": 0.9}
    suspect = {"threat_mean": 22, "threat_p95": 45, "neg_ratio": 0.25, "motion_p95": 0.12, "valid_ratio": 0.9, "face_presence_ratio": 0.9}
    threat = {"threat_mean": 45, "threat_p95": 80, "neg_ratio": 0.5, "motion_p95": 0.2, "valid_ratio": 0.9, "face_presence_ratio": 0.9}

    state, _ = fsm.update(0, calm, True, 0.9, 0.9)
    assert state == FSMState.CALM.value
    state, evt = fsm.update(1000, suspect, True, 0.9, 0.9)
    assert state == FSMState.SUSPECT.value and evt is not None
    state, _ = fsm.update(2000, calm, True, 0.9, 0.9)
    assert state == FSMState.SUSPECT.value  # min dwell suspect blocks exit
    state, _ = fsm.update(4500, threat, True, 0.9, 0.9)
    assert state == FSMState.THREAT.value
    state, _ = fsm.update(7000, calm, True, 0.9, 0.9)
    assert state == FSMState.THREAT.value  # min dwell threat not reached
    state, evt = fsm.update(10050, calm, True, 0.9, 0.9)
    assert state == FSMState.SUSPECT.value and evt is not None


def test_no_face_and_low_quality_timeouts():
    fsm = PersonFSM(_cfg())
    feat = {"threat_mean": 10, "threat_p95": 20, "neg_ratio": 0.1, "motion_p95": 0.05, "valid_ratio": 0.9, "face_presence_ratio": 0.9}
    fsm.update(0, feat, True, 0.9, 0.9)

    state, _ = fsm.update(2500, {**feat, "valid_ratio": 0.1}, True, 0.1, 0.9)
    assert state == FSMState.LOW_QUALITY.value

    state, _ = fsm.update(5000, feat, False, 0.9, 0.0)
    assert state == FSMState.NO_FACE.value
