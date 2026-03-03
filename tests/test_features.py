from faceguard.features import compute_features


def test_compute_features_basic():
    samples = [
        (0, True, "FACE", False, 0.1, [0.7,0.1,0.0,0.0,0.1,0.1,0.0,0.0], 20, True, 1000.0),
        (1000, True, "FACE", False, 0.2, [0.6,0.2,0.0,0.0,0.1,0.1,0.0,0.0], 30, False, 980.0),
        (2000, False, "PROFIL", True, 0.4, [0.2,0.1,0.1,0.3,0.1,0.1,0.1,0.0], 80, True, 900.0),
    ]
    out = compute_features(samples, 60000)
    assert out["sample_count"] == 3
    assert 0.0 <= out["valid_ratio"] <= 1.0
    assert out["motion_p95"] >= out["motion_mean"]
    assert "emo_top1_mode" in out
