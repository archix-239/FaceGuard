"""Multi-person face tracking with stable ID assignment.

Provides:
- NMS deduplication of raw MediaPipe detections
- Cost-based (IoU + distance + size) detection-to-person matching
- Anti-duplication guard: unmatched detections overlapping existing persons are suppressed
- Velocity-based bbox prediction for track-only frames
- Per-person state: prediction buffer, inference scheduling, landmarks
- TTL cleanup with configurable grace/reacquire window
"""

from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from faceguard.features import compute_features
from faceguard.fsm import PersonFSM


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------

def bbox_iou(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> float:
    """IoU between two (x, y, w, h) bboxes."""
    ax, ay, aw, ah = a
    bx, by, bw, bh = b

    x1 = max(ax, bx)
    y1 = max(ay, by)
    x2 = min(ax + aw, bx + bw)
    y2 = min(ay + ah, by + bh)

    inter = max(0, x2 - x1) * max(0, y2 - y1)
    union = aw * ah + bw * bh - inter
    return inter / union if union > 0 else 0.0


def bbox_center(bbox: tuple[int, int, int, int]) -> tuple[float, float]:
    """Center (cx, cy) of an (x, y, w, h) bbox."""
    x, y, w, h = bbox
    return (x + w / 2.0, y + h / 2.0)


def nms_bboxes(
    bboxes: list[tuple[int, int, int, int]],
    iou_threshold: float = 0.5,
) -> list[int]:
    """Non-maximum suppression.  Returns indices of bboxes to keep.

    Larger bboxes are kept preferentially (area as confidence proxy).
    """
    if not bboxes:
        return []

    indexed = sorted(
        range(len(bboxes)),
        key=lambda i: bboxes[i][2] * bboxes[i][3],
        reverse=True,
    )

    keep: list[int] = []
    suppressed: set[int] = set()

    for idx in indexed:
        if idx in suppressed:
            continue
        keep.append(idx)
        for other in indexed:
            if other == idx or other in suppressed:
                continue
            if bbox_iou(bboxes[idx], bboxes[other]) > iou_threshold:
                suppressed.add(other)

    return sorted(keep)


# ---------------------------------------------------------------------------
# Per-person state
# ---------------------------------------------------------------------------

@dataclass
class PersonState:
    person_id: int
    bbox: tuple[int, int, int, int]  # (x, y, w, h) full-image coords
    velocity: tuple[float, float] = (0.0, 0.0)  # px/ms
    last_seen_ts_ms: int = 0
    last_detect_ts_ms: int = 0
    missed_detect_count: int = 0
    preds_buffer: deque = field(default_factory=lambda: deque(maxlen=15))
    last_prediction: np.ndarray = field(
        default_factory=lambda: np.zeros(8, dtype=np.float32)
    )
    next_infer_ts_ms: int | None = None
    landmarks: Any = None
    tracker: Any = None  # OpenCV tracker, managed by caller
    _prev_center: tuple[float, float] | None = None
    _prev_center_ts_ms: int | None = None
    temporal_buffer: deque = field(default_factory=deque)
    last_features_ts_ms: int | None = None
    fsm: PersonFSM | None = None
    intent_state: str = "CALM"
    state_confidence: float = 0.0
    last_detect_area: float = 0.0

    def add_temporal_sample(
        self,
        ts_ms: int,
        valid: bool,
        pose: str,
        asym: bool,
        motion: float,
        emo_probs: np.ndarray,
        threat_frame: int,
        infer_ran: bool,
        bbox_area: float,
        window_ms: int,
    ) -> tuple[int, float]:
        probs = np.asarray(emo_probs, dtype=np.float32).tolist()
        self.temporal_buffer.append((
            int(ts_ms), bool(valid), str(pose), bool(asym), float(motion), probs,
            float(threat_frame), bool(infer_ran), float(bbox_area),
        ))
        self.trim_temporal_buffer(int(ts_ms), int(window_ms))
        return self.get_history_stats()

    def trim_temporal_buffer(self, now_ms: int, window_ms: int):
        min_ts = int(now_ms) - int(window_ms)
        while self.temporal_buffer and int(self.temporal_buffer[0][0]) < min_ts:
            self.temporal_buffer.popleft()

    def get_history_stats(self) -> tuple[int, float]:
        n = len(self.temporal_buffer)
        if n == 0:
            return 0, 0.0
        valid = sum(1 for s in self.temporal_buffer if bool(s[1]))
        return n, float(valid / n)

    def maybe_emit_features(self, clock_ts_ms: int, window_ms: int, features_hz: float):
        hz = max(1e-6, float(features_hz))
        period_ms = int(1000.0 / hz)
        if self.last_features_ts_ms is not None and (int(clock_ts_ms) - int(self.last_features_ts_ms)) < period_ms:
            return None
        self.trim_temporal_buffer(int(clock_ts_ms), int(window_ms))
        samples = list(self.temporal_buffer)
        feats = compute_features(samples, int(window_ms))
        self.last_features_ts_ms = int(clock_ts_ms)
        return {
            "ts_ms": int(clock_ts_ms),
            "person_id": int(self.person_id),
            "window_ms": int(window_ms),
            "features": feats,
        }


# ---------------------------------------------------------------------------
# Multi-person tracker
# ---------------------------------------------------------------------------

class MultiPersonTracker:
    """Stable multi-person ID tracker.

    Call ``update_with_detections`` on detection frames and
    ``update_track_only`` between detections.
    """

    def __init__(
        self,
        iou_min: float = 0.15,
        dist_max_norm: float = 0.4,
        size_penalty_weight: float = 0.3,
        reacquire_grace_ms: int = 1500,
        reacquire_multiplier: float = 1.5,
        ttl_ms: int = 3000,
        dedup_iou_threshold: float = 0.5,
        preds_buffer_maxlen: int = 15,
    ):
        self.iou_min = iou_min
        self.dist_max_norm = dist_max_norm
        self.size_penalty_weight = size_penalty_weight
        self.reacquire_grace_ms = reacquire_grace_ms
        self.reacquire_multiplier = reacquire_multiplier
        self.ttl_ms = ttl_ms
        self.dedup_iou_threshold = dedup_iou_threshold
        self.preds_buffer_maxlen = preds_buffer_maxlen

        self._next_id: int = 1
        self.persons: dict[int, PersonState] = {}

    # -- ID generation ------------------------------------------------------

    def _new_id(self) -> int:
        pid = self._next_id
        self._next_id += 1
        return pid

    # -- Prediction ---------------------------------------------------------

    def predict_bbox(
        self, person: PersonState, ts_ms: int
    ) -> tuple[int, int, int, int]:
        """Constant-velocity bbox prediction with capped displacement."""
        dt = ts_ms - person.last_seen_ts_ms
        if dt <= 0:
            return person.bbox
        x, y, w, h = person.bbox
        vx, vy = person.velocity
        # Cap displacement to 2x the bbox diagonal to prevent runaway predictions
        max_disp = 2.0 * math.hypot(w, h)
        dx = max(-max_disp, min(max_disp, vx * dt))
        dy = max(-max_disp, min(max_disp, vy * dt))
        return (int(x + dx), int(y + dy), w, h)

    # -- Matching cost ------------------------------------------------------

    def _match_cost(
        self,
        person: PersonState,
        det_bbox: tuple[int, int, int, int],
        frame_diag: float,
        ts_ms: int,
    ) -> float:
        pred_bbox = self.predict_bbox(person, ts_ms)
        # Also try matching against raw (non-predicted) bbox for robustness
        iou_pred = bbox_iou(pred_bbox, det_bbox)
        iou_raw = bbox_iou(person.bbox, det_bbox)
        iou = max(iou_pred, iou_raw)

        # Relax thresholds during reacquire grace window, progressively
        eff_iou_min = self.iou_min
        eff_dist_max = self.dist_max_norm
        grace_active = (
            person.missed_detect_count > 0
            and (ts_ms - person.last_detect_ts_ms) <= self.reacquire_grace_ms
        )
        if grace_active:
            # Progressive relaxation: more misses = wider search (up to 3x)
            miss_scale = 1.0 + min(person.missed_detect_count, 10) * 0.2
            eff_iou_min = self.iou_min / (self.reacquire_multiplier * miss_scale)
            eff_dist_max = self.dist_max_norm * self.reacquire_multiplier * miss_scale

        # Use best center (predicted or raw) for distance computation
        pc_pred = bbox_center(pred_bbox)
        pc_raw = bbox_center(person.bbox)
        dc = bbox_center(det_bbox)
        dist_pred = math.hypot(pc_pred[0] - dc[0], pc_pred[1] - dc[1])
        dist_raw = math.hypot(pc_raw[0] - dc[0], pc_raw[1] - dc[1])
        dist = min(dist_pred, dist_raw)
        dist_norm = dist / max(frame_diag, 1.0)

        area_p = max(pred_bbox[2] * pred_bbox[3], 1)
        area_d = max(det_bbox[2] * det_bbox[3], 1)
        size_ratio = max(area_p, area_d) / min(area_p, area_d)
        size_penalty = (size_ratio - 1.0) * self.size_penalty_weight

        # Gate: reject if both IoU too low AND distance too large
        if iou < eff_iou_min and dist_norm > eff_dist_max:
            return float("inf")

        return (1.0 - iou) + dist_norm + size_penalty

    # -- Full detection update ----------------------------------------------

    def update_with_detections(
        self,
        detections: list[tuple[int, int, int, int]],
        landmarks_list: list[Any],
        ts_ms: int,
        frame_w: int,
        frame_h: int,
    ) -> dict:
        """NMS + match + create/expire.  Returns diagnostics dict."""
        frame_diag = math.hypot(frame_w, frame_h)
        raw_det_count = len(detections)

        # 1. NMS dedup
        keep = nms_bboxes(detections, self.dedup_iou_threshold)
        detections = [detections[i] for i in keep]
        landmarks_list = [landmarks_list[i] for i in keep]
        kept_det_count = len(detections)

        # 2. Build cost matrix
        pids = list(self.persons.keys())
        n_p = len(pids)
        n_d = len(detections)

        match_events: list[dict] = []
        new_ids_created: list[dict] = []
        matched_dets: set[int] = set()
        matched_persons: set[int] = set()

        if n_p > 0 and n_d > 0:
            costs = np.full((n_p, n_d), float("inf"))
            for i, pid in enumerate(pids):
                for j in range(n_d):
                    costs[i, j] = self._match_cost(
                        self.persons[pid], detections[j], frame_diag, ts_ms
                    )

            # 3. Greedy assignment (lowest cost first)
            flat = []
            for i in range(n_p):
                for j in range(n_d):
                    c = costs[i, j]
                    if c < float("inf"):
                        flat.append((c, i, j))
            flat.sort()

            for cost, i, j in flat:
                if i in matched_persons or j in matched_dets:
                    continue
                pid = pids[i]
                pred = self.predict_bbox(self.persons[pid], ts_ms)
                iou_val = bbox_iou(pred, detections[j])
                self._update_person(pid, detections[j], landmarks_list[j], ts_ms)
                matched_persons.add(i)
                matched_dets.add(j)
                match_events.append({
                    "person_id": pid,
                    "det_idx": j,
                    "cost": round(cost, 4),
                    "iou": round(iou_val, 4),
                })

        # 4. Unmatched persons -> velocity prediction, increment miss
        for i, pid in enumerate(pids):
            if i in matched_persons:
                continue
            person = self.persons[pid]
            person.missed_detect_count += 1
            person.bbox = self.predict_bbox(person, ts_ms)
            person.last_seen_ts_ms = ts_ms
            person.tracker = None

        # 5. Unmatched detections -> new IDs (with anti-duplication guard)
        for j in range(n_d):
            if j in matched_dets:
                continue
            # Suppress if overlaps ANY current person bbox
            overlap = False
            for person in self.persons.values():
                if bbox_iou(person.bbox, detections[j]) > self.dedup_iou_threshold * 0.6:
                    overlap = True
                    break
            if overlap:
                continue
            new_pid = self._create_person(
                detections[j], landmarks_list[j], ts_ms
            )
            new_ids_created.append({
                "person_id": new_pid,
                "det_idx": j,
                "bbox": list(detections[j]),
            })

        # 6. TTL cleanup
        expired = self.cleanup_expired(ts_ms)

        return {
            "raw_dets": raw_det_count,
            "kept_dets": kept_det_count,
            "active_persons": len(self.persons),
            "match_events": match_events,
            "new_ids_created": new_ids_created,
            "expired_ids": expired,
            "unmatched_dets": n_d - len(matched_dets),
        }

    # -- Track-only update --------------------------------------------------

    def cleanup_expired(self, ts_ms: int) -> list[int]:
        """Remove persons whose last detection exceeds TTL."""
        expired = [
            pid
            for pid, p in self.persons.items()
            if (ts_ms - p.last_detect_ts_ms) > self.ttl_ms
        ]
        for pid in expired:
            del self.persons[pid]
        return expired

    # -- Internal helpers ---------------------------------------------------

    def _update_person(
        self,
        pid: int,
        bbox: tuple[int, int, int, int],
        landmarks: Any,
        ts_ms: int,
    ) -> None:
        person = self.persons[pid]
        new_c = bbox_center(bbox)
        if person._prev_center is not None and person._prev_center_ts_ms is not None:
            dt = ts_ms - person._prev_center_ts_ms
            if dt > 0:
                vx = (new_c[0] - person._prev_center[0]) / dt
                vy = (new_c[1] - person._prev_center[1]) / dt
                a = 0.6
                person.velocity = (
                    a * vx + (1 - a) * person.velocity[0],
                    a * vy + (1 - a) * person.velocity[1],
                )

        person._prev_center = new_c
        person._prev_center_ts_ms = ts_ms
        person.bbox = bbox
        person.landmarks = landmarks
        person.last_seen_ts_ms = ts_ms
        person.last_detect_ts_ms = ts_ms
        person.missed_detect_count = 0
        person.last_detect_area = float(max(1, bbox[2] * bbox[3]))

    def _create_person(
        self,
        bbox: tuple[int, int, int, int],
        landmarks: Any,
        ts_ms: int,
    ) -> int:
        pid = self._new_id()
        self.persons[pid] = PersonState(
            person_id=pid,
            bbox=bbox,
            last_seen_ts_ms=ts_ms,
            last_detect_ts_ms=ts_ms,
            preds_buffer=deque(maxlen=self.preds_buffer_maxlen),
            landmarks=landmarks,
            _prev_center=bbox_center(bbox),
            _prev_center_ts_ms=ts_ms,
            last_detect_area=float(max(1, bbox[2] * bbox[3])),
        )
        return pid
