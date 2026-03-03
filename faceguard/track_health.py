from __future__ import annotations

from typing import Any


def _oob_ratio(bbox: tuple[int, int, int, int], img_w: int, img_h: int) -> float:
    x, y, w, h = bbox
    x2 = x + w
    y2 = y + h
    inter_x1 = max(0, x)
    inter_y1 = max(0, y)
    inter_x2 = min(img_w, x2)
    inter_y2 = min(img_h, y2)
    inter_w = max(0, inter_x2 - inter_x1)
    inter_h = max(0, inter_y2 - inter_y1)
    inter_area = inter_w * inter_h
    area = max(1, w * h)
    return max(0.0, min(1.0, 1.0 - (inter_area / area)))


def evaluate_tracking_health(person: Any, img_w: int, img_h: int, cfg: dict[str, float]) -> tuple[bool, str]:
    if getattr(person, "tracker", None) is None:
        return False, "tracker_none"

    x, y, w, h = person.bbox
    if w <= 0 or h <= 0:
        return False, "bbox_invalid"

    oob = _oob_ratio(person.bbox, img_w, img_h)
    if oob > float(cfg.get("max_oob_ratio", 0.2)):
        return False, "bbox_oob"

    area = float(max(1, w * h))
    ref_area = float(getattr(person, "last_detect_area", area))
    if ref_area > 0:
        ratio = area / ref_area
        if ratio > float(cfg.get("max_area_ratio", 2.5)) or ratio < float(cfg.get("min_area_ratio", 0.4)):
            return False, "bbox_area_jump"

    cx = x + (w / 2.0)
    cy = y + (h / 2.0)
    prev_center = getattr(person, "_prev_center", None)
    if prev_center is not None:
        dx = cx - float(prev_center[0])
        dy = cy - float(prev_center[1])
        center_jump = (dx * dx + dy * dy) ** 0.5
        if center_jump > float(cfg.get("max_center_jump_px", 80.0)):
            return False, "center_jump"

    if int(getattr(person, "missed_detect_count", 0)) >= int(cfg.get("max_missed_detects_before_redetect", 3)):
        return False, "missed_detects"

    return True, "ok"
