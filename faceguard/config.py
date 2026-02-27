from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, Dict

import yaml


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_PATH = REPO_ROOT / "configs" / "default.yaml"


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    result = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _resolve_repo_path(value: str) -> str:
    path = Path(value)
    if path.is_absolute():
        return str(path)
    return str((REPO_ROOT / path).resolve())


def _apply_path_resolution(config: Dict[str, Any]) -> Dict[str, Any]:
    out = deepcopy(config)
    out["models"]["emotion_model_path"] = _resolve_repo_path(out["models"]["emotion_model_path"])
    out["models"]["face_landmarker_path"] = _resolve_repo_path(out["models"]["face_landmarker_path"])
    inference_cfg = out.get("inference", {})
    tflite_model_path = inference_cfg.get("tflite_model_path")
    if tflite_model_path:
        inference_cfg["tflite_model_path"] = _resolve_repo_path(str(tflite_model_path))
    out["inference"] = inference_cfg

    tracking_cfg = out.get("tracking", {})
    tracking_cfg.setdefault("max_faces", 2)
    tracking_cfg.setdefault("ttl_ms", 2000)
    tracking_cfg.setdefault("iou_match_threshold", 0.2)
    tracking_cfg.setdefault("centroid_match_threshold", 0.15)
    out["tracking"] = tracking_cfg
    return out


def load_config(path: str | None = None) -> Dict[str, Any]:
    with DEFAULT_CONFIG_PATH.open("r", encoding="utf-8") as f:
        default_cfg = yaml.safe_load(f) or {}

    if path:
        cfg_path = Path(path)
        if not cfg_path.is_absolute():
            cfg_path = (REPO_ROOT / cfg_path).resolve()
        with cfg_path.open("r", encoding="utf-8") as f:
            user_cfg = yaml.safe_load(f) or {}
        merged = _deep_merge(default_cfg, user_cfg)
    else:
        merged = default_cfg

    return _apply_path_resolution(merged)
