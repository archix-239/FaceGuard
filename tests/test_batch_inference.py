"""Tests for batched inference in InferenceBackend.

Mocks tensorflow so tests can run without the full TF dependency.
"""

from __future__ import annotations

import sys
import time
from unittest.mock import MagicMock

# Mock tensorflow before importing the backend module
sys.modules.setdefault("tensorflow", MagicMock())
sys.modules.setdefault("tensorflow.keras", MagicMock())
sys.modules.setdefault("tensorflow.keras.models", MagicMock())
sys.modules.setdefault("tensorflow.lite", MagicMock())

import numpy as np
import pytest

from faceguard.services.inference_backend import InferenceBackend


# ---------------------------------------------------------------------------
# Stub backends used for testing
# ---------------------------------------------------------------------------

class _FakeSequentialBackend(InferenceBackend):
    """Simulates a backend that does NOT support native batching (e.g. TFLite).

    Each ``predict`` call has a small artificial delay to make the
    latency difference between sequential and batched measurable.
    """

    NUM_CLASSES = 8

    def __init__(self, delay_s: float = 0.005):
        self._delay = delay_s
        self.predict_call_count = 0

    def predict(self, tensor: np.ndarray) -> np.ndarray:
        self.predict_call_count += 1
        time.sleep(self._delay)
        mean_val = float(np.mean(tensor))
        out = np.full(self.NUM_CLASSES, mean_val / self.NUM_CLASSES, dtype=np.float32)
        out[0] = mean_val
        return out


class _FakeBatchBackend(InferenceBackend):
    """Simulates a backend that DOES support native batching (e.g. Keras).

    A single ``predict_batch`` call handles the entire batch with one
    fixed-cost delay regardless of N, while ``predict`` has per-sample cost.
    """

    NUM_CLASSES = 8

    def __init__(self, per_sample_delay: float = 0.005, batch_delay: float = 0.008):
        self._per_sample_delay = per_sample_delay
        self._batch_delay = batch_delay
        self.predict_call_count = 0
        self.predict_batch_call_count = 0

    @property
    def supports_batch(self) -> bool:
        return True

    def predict(self, tensor: np.ndarray) -> np.ndarray:
        self.predict_call_count += 1
        time.sleep(self._per_sample_delay)
        mean_val = float(np.mean(tensor))
        out = np.full(self.NUM_CLASSES, mean_val / self.NUM_CLASSES, dtype=np.float32)
        out[0] = mean_val
        return out

    def predict_batch(self, batch: np.ndarray) -> np.ndarray:
        self.predict_batch_call_count += 1
        time.sleep(self._batch_delay)
        n = batch.shape[0]
        results = np.zeros((n, self.NUM_CLASSES), dtype=np.float32)
        for i in range(n):
            mean_val = float(np.mean(batch[i]))
            results[i] = mean_val / self.NUM_CLASSES
            results[i, 0] = mean_val
        return results


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def _make_batch(n: int, h: int = 48, w: int = 48, c: int = 3) -> np.ndarray:
    rng = np.random.RandomState(42)
    return rng.rand(n, h, w, c).astype(np.float32)


class TestBaseBackendFallback:
    """The base InferenceBackend.predict_batch should fall back to a loop."""

    def test_single_sample(self):
        backend = _FakeSequentialBackend(delay_s=0.0)
        batch = _make_batch(1)
        result = backend.predict_batch(batch)
        assert result.shape == (1, 8)
        assert backend.predict_call_count == 1

    def test_multiple_samples(self):
        backend = _FakeSequentialBackend(delay_s=0.0)
        batch = _make_batch(4)
        result = backend.predict_batch(batch)
        assert result.shape == (4, 8)
        assert backend.predict_call_count == 4

    def test_results_match_individual_calls(self):
        backend = _FakeSequentialBackend(delay_s=0.0)
        batch = _make_batch(3)
        batched = backend.predict_batch(batch)

        backend2 = _FakeSequentialBackend(delay_s=0.0)
        individual = np.stack(
            [backend2.predict(batch[i : i + 1]) for i in range(3)], axis=0
        )
        np.testing.assert_array_almost_equal(batched, individual)


class TestNativeBatchBackend:
    """A backend that supports native batching should use predict_batch."""

    def test_supports_batch_flag(self):
        backend = _FakeBatchBackend()
        assert backend.supports_batch is True

    def test_base_does_not_support_batch(self):
        backend = _FakeSequentialBackend()
        assert backend.supports_batch is False

    def test_batch_single_call(self):
        backend = _FakeBatchBackend(per_sample_delay=0.0, batch_delay=0.0)
        batch = _make_batch(4)
        result = backend.predict_batch(batch)
        assert result.shape == (4, 8)
        assert backend.predict_batch_call_count == 1
        assert backend.predict_call_count == 0

    def test_batch_results_match_individual(self):
        backend = _FakeBatchBackend(per_sample_delay=0.0, batch_delay=0.0)
        batch = _make_batch(3)
        batched = backend.predict_batch(batch)

        individual = np.stack(
            [backend.predict(batch[i : i + 1]) for i in range(3)], axis=0
        )
        np.testing.assert_array_almost_equal(batched, individual)


class TestBatchLatencyBenefit:
    """Batched inference should be faster than sequential when N > 1."""

    def test_batch_faster_than_sequential(self):
        n = 4
        per_sample_ms = 10  # 10 ms per sample
        batch = _make_batch(n)

        # Sequential: N individual calls
        seq_backend = _FakeSequentialBackend(delay_s=per_sample_ms / 1000.0)
        t0 = time.perf_counter()
        for i in range(n):
            seq_backend.predict(batch[i : i + 1])
        sequential_time = time.perf_counter() - t0

        # Batched: single predict_batch call (fixed cost ~1.2x single sample)
        batch_backend = _FakeBatchBackend(
            per_sample_delay=per_sample_ms / 1000.0,
            batch_delay=per_sample_ms / 1000.0 * 1.2,
        )
        t0 = time.perf_counter()
        batch_backend.predict_batch(batch)
        batched_time = time.perf_counter() - t0

        # Batched should be significantly faster for N=4
        assert batched_time < sequential_time, (
            f"Batch ({batched_time*1000:.1f}ms) should be faster than "
            f"sequential ({sequential_time*1000:.1f}ms) for N={n}"
        )

    def test_fallback_loop_same_result_count(self):
        """Fallback loop (base class) still produces correct N outputs."""
        n = 3
        backend = _FakeSequentialBackend(delay_s=0.0)
        batch = _make_batch(n)
        result = backend.predict_batch(batch)
        assert result.shape[0] == n


class TestEdgeCases:
    """Edge cases for batched inference."""

    def test_single_face_no_regression(self):
        """Single-face batch should match the original predict() output."""
        backend = _FakeSequentialBackend(delay_s=0.0)
        batch = _make_batch(1)
        batched = backend.predict_batch(batch)
        single = backend.predict(batch[0:1])
        np.testing.assert_array_almost_equal(batched[0], single)

    def test_large_batch(self):
        """Batch with many faces should still work."""
        backend = _FakeSequentialBackend(delay_s=0.0)
        batch = _make_batch(10)
        result = backend.predict_batch(batch)
        assert result.shape == (10, 8)
