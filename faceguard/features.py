from __future__ import annotations

import math
from collections import Counter


NEGATIVE_EMOTIONS = {"ANGRY", "CONTEMPT", "FEAR", "DISGUST", "SAD"}


def softmax_entropy(probs: list[float]) -> float:
    eps = 1e-12
    ent = 0.0
    for p in probs:
        p = max(float(p), eps)
        ent -= p * math.log(p)
    return ent


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return float(values[0])
    arr = sorted(float(v) for v in values)
    k = (len(arr) - 1) * p
    f = int(math.floor(k))
    c = int(math.ceil(k))
    if f == c:
        return arr[f]
    return arr[f] * (c - k) + arr[c] * (k - f)


def trend_slope(ts_ms: list[int], values: list[float]) -> float:
    if len(ts_ms) < 2 or len(values) < 2:
        return 0.0
    t0 = float(ts_ms[0])
    xs = [(float(t) - t0) / 1000.0 for t in ts_ms]
    ys = [float(v) for v in values]
    mx = sum(xs) / len(xs)
    my = sum(ys) / len(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = sum((x - mx) ** 2 for x in xs)
    if den <= 1e-12:
        return 0.0
    return num / den


def compute_features(samples: list[tuple], window_ms: int) -> dict:
    if not samples:
        return {
            "window_ms": int(window_ms),
            "sample_count": 0,
            "valid_ratio": 0.0,
            "face_presence_ratio": 0.0,
        }

    n = len(samples)
    valid_count = sum(1 for s in samples if bool(s[1]))

    top1_labels: list[str] = []
    entropies: list[float] = []
    volatilities: list[float] = []
    motions: list[float] = []
    bbox_areas: list[float] = []
    ts_list: list[int] = []
    poses: list[str] = []
    threats: list[float] = []

    prev_probs: list[float] | None = None
    for ts_ms, _valid, pose, _asym, motion, emo_probs, threat_frame, _infer_ran, bbox_area in samples:
        ts_list.append(int(ts_ms))
        poses.append(str(pose))
        motions.append(float(motion))
        bbox_areas.append(float(bbox_area))
        threats.append(float(threat_frame))
        probs = [float(x) for x in emo_probs]

        if probs:
            top_idx = max(range(len(probs)), key=lambda i: probs[i])
            emo_names = ["ANGRY", "CONTEMPT", "DISGUST", "FEAR", "HAPPY", "NEUTRAL", "SAD", "SURPRISE"]
            top1_labels.append(emo_names[top_idx] if top_idx < len(emo_names) else str(top_idx))
            entropies.append(softmax_entropy(probs))
            if prev_probs is not None and len(prev_probs) == len(probs):
                volatilities.append(sum(abs(a - b) for a, b in zip(probs, prev_probs)))
            prev_probs = probs

    pose_transitions = sum(1 for i in range(1, len(poses)) if poses[i] != poses[i - 1])
    duration_ms = max(1, ts_list[-1] - ts_list[0])
    transitions_per_min = pose_transitions / (duration_ms / 60000.0)

    top1_counter = Counter(top1_labels)
    mode_label = top1_counter.most_common(1)[0][0] if top1_counter else "SCANNING..."

    negative_count = sum(1 for label in top1_labels if label in NEGATIVE_EMOTIONS)
    anger_count = sum(1 for label in top1_labels if label == "ANGRY")
    fear_count = sum(1 for label in top1_labels if label == "FEAR")

    threat_over_70 = sum(1 for t in threats if t >= 70.0)

    return {
        "window_ms": int(window_ms),
        "sample_count": n,
        "emo_top1_mode": mode_label,
        "emo_entropy_mean": float(sum(entropies) / len(entropies)) if entropies else 0.0,
        "emo_volatility_mean": float(sum(volatilities) / len(volatilities)) if volatilities else 0.0,
        "neg_ratio": float(negative_count / len(top1_labels)) if top1_labels else 0.0,
        "anger_ratio": float(anger_count / len(top1_labels)) if top1_labels else 0.0,
        "fear_ratio": float(fear_count / len(top1_labels)) if top1_labels else 0.0,
        "motion_mean": float(sum(motions) / len(motions)) if motions else 0.0,
        "motion_p95": float(percentile(motions, 0.95)) if motions else 0.0,
        "bbox_area_mean": float(sum(bbox_areas) / len(bbox_areas)) if bbox_areas else 0.0,
        "bbox_area_trend": float(trend_slope(ts_list, bbox_areas)) if bbox_areas else 0.0,
        "pose_face_ratio": float(sum(1 for p in poses if p == "FACE") / len(poses)) if poses else 0.0,
        "pose_instability": float(transitions_per_min),
        "valid_ratio": float(valid_count / n),
        "face_presence_ratio": 1.0,
        "threat_mean": float(sum(threats) / len(threats)) if threats else 0.0,
        "threat_p95": float(percentile(threats, 0.95)) if threats else 0.0,
        "threat_time_over_70_ratio": float(threat_over_70 / len(threats)) if threats else 0.0,
    }

