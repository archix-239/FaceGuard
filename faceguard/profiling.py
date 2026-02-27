from __future__ import annotations

import json
import os
import statistics
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional


class Timer:
    """Context manager to measure a named timing block in milliseconds."""

    def __init__(self, timings_ms: Dict[str, float], name: str):
        self.timings_ms = timings_ms
        self.name = name
        self._start = 0.0

    def __enter__(self):
        self._start = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc, tb):
        elapsed_ms = (time.perf_counter() - self._start) * 1000.0
        self.timings_ms[self.name] = elapsed_ms
        return False


@dataclass
class FrameTimings:
    ts_ms: int
    frame_idx: int
    has_face: bool = False
    pose: str = "INCONNU"
    valid_quality: bool = False
    infer_ran: bool = False
    detect_ran: bool = False
    tracker_ran: bool = False
    track_ok: bool = False
    need_detect_reason: str = ""
    detect_every_ms: float | None = None
    bbox: list[int] | None = None
    timings_ms: Dict[str, float] = field(default_factory=dict)
    emotion_top1: str = "SCANNING..."
    emotion_p: float = 0.0
    threat_score: int = 0
    people: list[dict] = field(default_factory=list)
    match_events: list[dict] = field(default_factory=list)
    new_ids_created: int = 0
    unmatched_dets: int = 0

    def to_json_line(self) -> str:
        payload = {
            "ts_ms": self.ts_ms,
            "frame_idx": self.frame_idx,
            "has_face": self.has_face,
            "pose": self.pose,
            "valid_quality": self.valid_quality,
            "infer_ran": self.infer_ran,
            "detect_ran": self.detect_ran,
            "tracker_ran": self.tracker_ran,
            "track_ok": self.track_ok,
            "need_detect_reason": self.need_detect_reason,
            "detect_every_ms": self.detect_every_ms,
            "bbox": self.bbox,
            "timings_ms": self.timings_ms,
            "emotion_top1": self.emotion_top1,
            "emotion_p": self.emotion_p,
            "threat_score": self.threat_score,
            "people": self.people,
            "match_events": self.match_events,
            "new_ids_created": self.new_ids_created,
            "unmatched_dets": self.unmatched_dets,
        }
        return json.dumps(payload, ensure_ascii=False)


class RunProfiler:
    def __init__(
        self,
        logs_dir: str = "logs",
        flush_every_n: int = 30,
        output_path: Optional[str] = None,
    ):
        if output_path is not None:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            self.path = output_path
        else:
            os.makedirs(logs_dir, exist_ok=True)
            ts = time.strftime("%Y%m%d_%H%M%S")
            self.path = os.path.join(logs_dir, f"run_{ts}.jsonl")

        self._fh = open(self.path, "w", encoding="utf-8")
        self._flush_every_n = max(1, flush_every_n)
        self._write_count = 0
        self._stats: Dict[str, List[float]] = {
            "capture": [],
            "mediapipe": [],
            "tracker": [],
            "preprocess": [],
            "infer": [],
            "ui": [],
            "total": [],
        }

    def write_frame(self, frame: FrameTimings):
        self._fh.write(frame.to_json_line() + "\n")
        self._write_count += 1
        if self._write_count % self._flush_every_n == 0:
            self._fh.flush()
        for key in self._stats:
            if key in frame.timings_ms:
                self._stats[key].append(frame.timings_ms[key])

    def _fmt_percentiles(self, values: List[float]) -> str:
        if not values:
            return "p50=n/a p90=n/a p99=n/a"

        def percentile(sorted_vals: List[float], p: float) -> float:
            if len(sorted_vals) == 1:
                return sorted_vals[0]
            k = (len(sorted_vals) - 1) * p
            f = int(k)
            c = min(f + 1, len(sorted_vals) - 1)
            if f == c:
                return sorted_vals[f]
            d0 = sorted_vals[f] * (c - k)
            d1 = sorted_vals[c] * (k - f)
            return d0 + d1

        arr = sorted(values)
        p50 = percentile(arr, 0.50)
        p90 = percentile(arr, 0.90)
        p99 = percentile(arr, 0.99)
        return f"p50={p50:.2f}ms p90={p90:.2f}ms p99={p99:.2f}ms"

    def print_summary(self):
        print("\n" + "=" * 50)
        print("📊 PROFILING SUMMARY")
        print("(note: total = total_processing thread)")
        print(f"JSONL: {self.path}")
        for stage in ["capture", "mediapipe", "tracker", "preprocess", "infer", "ui", "total"]:
            print(f"- {stage:10s}: {self._fmt_percentiles(self._stats[stage])}")

        totals = self._stats["total"]
        if totals:
            avg_total_ms = float(statistics.fmean(totals))
            avg_fps = 1000.0 / avg_total_ms if avg_total_ms > 0 else 0.0
            print(f"- {'avg_fps':10s}: {avg_fps:.2f}")
        else:
            print(f"- {'avg_fps':10s}: n/a")
        print("=" * 50 + "\n")

    def close(self):
        if not self._fh.closed:
            self._fh.flush()
            self._fh.close()
