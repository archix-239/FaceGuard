from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class FSMState(str, Enum):
    NO_FACE = "NO_FACE"
    LOW_QUALITY = "LOW_QUALITY"
    CALM = "CALM"
    SUSPECT = "SUSPECT"
    THREAT = "THREAT"


@dataclass
class FSMConfig:
    enabled: bool
    min_dwell_calm_ms: int
    min_dwell_suspect_ms: int
    min_dwell_threat_ms: int
    suspect_enter: dict[str, float]
    suspect_exit: dict[str, float]
    threat_enter: dict[str, float]
    threat_exit: dict[str, float]
    min_valid_ratio: float
    min_face_presence_ratio: float
    no_face_timeout_ms: int
    low_quality_timeout_ms: int

    @classmethod
    def from_dict(cls, cfg: dict[str, Any], fallback_min_valid_ratio: float) -> "FSMConfig":
        min_dwell = cfg.get("min_dwell_ms", {})
        thresholds = cfg.get("thresholds", {})
        quality_gate = cfg.get("quality_gate", {})
        return cls(
            enabled=bool(cfg.get("enabled", True)),
            min_dwell_calm_ms=int(min_dwell.get("calm", 2000)),
            min_dwell_suspect_ms=int(min_dwell.get("suspect", 3000)),
            min_dwell_threat_ms=int(min_dwell.get("threat", 5000)),
            suspect_enter=dict(thresholds.get("suspect_enter", {})),
            suspect_exit=dict(thresholds.get("suspect_exit", {})),
            threat_enter=dict(thresholds.get("threat_enter", {})),
            threat_exit=dict(thresholds.get("threat_exit", {})),
            min_valid_ratio=float(quality_gate.get("min_valid_ratio", fallback_min_valid_ratio)),
            min_face_presence_ratio=float(quality_gate.get("min_face_presence_ratio", 0.30)),
            no_face_timeout_ms=int(cfg.get("no_face_timeout_ms", 1500)),
            low_quality_timeout_ms=int(cfg.get("low_quality_timeout_ms", 2000)),
        )


class PersonFSM:
    def __init__(self, cfg: FSMConfig):
        self.cfg = cfg
        self.state = FSMState.CALM
        self.state_since_ts = -1
        self.last_seen_face_ts = -1
        self.last_good_quality_ts = -1

    def _dwell_required(self, state: FSMState) -> int:
        if state == FSMState.THREAT:
            return self.cfg.min_dwell_threat_ms
        if state == FSMState.SUSPECT:
            return self.cfg.min_dwell_suspect_ms
        return self.cfg.min_dwell_calm_ms

    @staticmethod
    def _meets_enter(features: dict[str, Any], thresholds: dict[str, float]) -> bool:
        return (
            float(features.get("threat_mean", 0.0)) >= float(thresholds.get("threat_mean_min", 0.0))
            and float(features.get("neg_ratio", 0.0)) >= float(thresholds.get("neg_ratio_min", 0.0))
            and float(features.get("motion_p95", 0.0)) >= float(thresholds.get("motion_p95_min", 0.0))
            and float(features.get("threat_p95", 0.0)) >= float(thresholds.get("threat_p95_min", 0.0))
        )

    @staticmethod
    def _meets_exit(features: dict[str, Any], thresholds: dict[str, float]) -> bool:
        t_mean_ok = float(features.get("threat_mean", 0.0)) <= float(thresholds.get("threat_mean_max", 1e9))
        n_ok = float(features.get("neg_ratio", 0.0)) <= float(thresholds.get("neg_ratio_max", 1e9))
        m_ok = float(features.get("motion_p95", 0.0)) <= float(thresholds.get("motion_p95_max", 1e9))
        tp95_ok = float(features.get("threat_p95", 0.0)) <= float(thresholds.get("threat_p95_max", 1e9))
        return t_mean_ok and n_ok and m_ok and tp95_ok

    def _transition(self, ts_ms: int, to_state: FSMState, reason: str, features: dict[str, Any], thresholds: dict[str, Any]) -> dict[str, Any] | None:
        if to_state == self.state:
            return None
        dwell_ms = max(0, int(ts_ms) - int(self.state_since_ts))
        event = {
            "type": "fsm_transition",
            "ts_ms": int(ts_ms),
            "from": self.state.value,
            "to": to_state.value,
            "reason": reason,
            "dwell_ms": int(dwell_ms),
            "features": {
                "threat_mean": float(features.get("threat_mean", 0.0)),
                "threat_p95": float(features.get("threat_p95", 0.0)),
                "neg_ratio": float(features.get("neg_ratio", 0.0)),
                "motion_p95": float(features.get("motion_p95", 0.0)),
                "valid_ratio": float(features.get("valid_ratio", 0.0)),
                "face_presence_ratio": float(features.get("face_presence_ratio", 0.0)),
            },
            "thresholds": dict(thresholds),
        }
        self.state = to_state
        self.state_since_ts = int(ts_ms)
        return event

    def update(self, ts_ms: int, features: dict[str, Any], has_face: bool, valid_ratio: float, face_presence_ratio: float):
        if self.state_since_ts < 0:
            self.state_since_ts = int(ts_ms)
            self.last_seen_face_ts = int(ts_ms)
            self.last_good_quality_ts = int(ts_ms)

        if has_face and face_presence_ratio >= self.cfg.min_face_presence_ratio:
            self.last_seen_face_ts = int(ts_ms)
        if valid_ratio >= self.cfg.min_valid_ratio:
            self.last_good_quality_ts = int(ts_ms)

        # gating states first
        if (int(ts_ms) - int(self.last_seen_face_ts)) >= self.cfg.no_face_timeout_ms:
            evt = self._transition(ts_ms, FSMState.NO_FACE, "no_face_timeout", features, {
                "no_face_timeout_ms": self.cfg.no_face_timeout_ms,
                "min_face_presence_ratio": self.cfg.min_face_presence_ratio,
            })
            return self.state.value, evt

        if (int(ts_ms) - int(self.last_good_quality_ts)) >= self.cfg.low_quality_timeout_ms:
            evt = self._transition(ts_ms, FSMState.LOW_QUALITY, "low_quality_timeout", features, {
                "low_quality_timeout_ms": self.cfg.low_quality_timeout_ms,
                "min_valid_ratio": self.cfg.min_valid_ratio,
            })
            return self.state.value, evt

        # recover from gates
        if self.state in (FSMState.NO_FACE, FSMState.LOW_QUALITY):
            evt = self._transition(ts_ms, FSMState.CALM, "quality_recovered", features, {})
            return self.state.value, evt

        dwell_ms = int(ts_ms) - int(self.state_since_ts)

        if self.state == FSMState.CALM:
            if self._meets_enter(features, self.cfg.threat_enter):
                evt = self._transition(ts_ms, FSMState.SUSPECT, "threat_signal_step_up", features, self.cfg.threat_enter)
                return self.state.value, evt
            if self._meets_enter(features, self.cfg.suspect_enter):
                evt = self._transition(ts_ms, FSMState.SUSPECT, "suspect_enter", features, self.cfg.suspect_enter)
                return self.state.value, evt
            return self.state.value, None

        if self.state == FSMState.SUSPECT:
            if self._meets_enter(features, self.cfg.threat_enter):
                evt = self._transition(ts_ms, FSMState.THREAT, "threat_enter", features, self.cfg.threat_enter)
                return self.state.value, evt
            if dwell_ms >= self.cfg.min_dwell_suspect_ms and self._meets_exit(features, self.cfg.suspect_exit):
                evt = self._transition(ts_ms, FSMState.CALM, "suspect_exit", features, self.cfg.suspect_exit)
                return self.state.value, evt
            return self.state.value, None

        if self.state == FSMState.THREAT:
            if dwell_ms >= self.cfg.min_dwell_threat_ms and self._meets_exit(features, self.cfg.threat_exit):
                evt = self._transition(ts_ms, FSMState.SUSPECT, "threat_exit", features, self.cfg.threat_exit)
                return self.state.value, evt
            return self.state.value, None

        return self.state.value, None
