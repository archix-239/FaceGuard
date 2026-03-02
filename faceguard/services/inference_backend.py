from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import tensorflow as tf


@dataclass
class InferenceDetails:
    backend: str
    model_path: str
    input_shape: Any
    input_dtype: str
    output_shape: Any
    output_dtype: str


class InferenceBackend:
    @property
    def supports_batch(self) -> bool:
        """Return True if this backend benefits from batched inference."""
        return False

    def predict(self, tensor: np.ndarray) -> np.ndarray:
        raise NotImplementedError

    def predict_batch(self, batch: np.ndarray) -> np.ndarray:
        """Predict on a batch of N samples.

        *batch* has shape ``(N, H, W, C)``.
        Returns an ``(N, num_classes)`` array.

        The default implementation loops over individual samples which is
        used as a fallback when the backend does not support native batching.
        """
        n = batch.shape[0]
        results = [self.predict(batch[i : i + 1]) for i in range(n)]
        return np.stack(results, axis=0)

    def details(self) -> InferenceDetails:
        raise NotImplementedError

    def warmup(self, input_shape: tuple[int, ...], runs: int):
        runs = max(0, int(runs))
        if runs == 0:
            return
        dummy = np.zeros(input_shape, dtype=np.float32)
        for _ in range(runs):
            _ = self.predict(dummy)


class KerasInferenceBackend(InferenceBackend):
    def __init__(self, model_path: str):
        self.model_path = model_path
        self.model = tf.keras.models.load_model(model_path, compile=False)
        input_shape = tuple(self.model.input_shape)
        output_shape = tuple(self.model.output_shape)
        self._details = InferenceDetails(
            backend="keras",
            model_path=model_path,
            input_shape=input_shape,
            input_dtype="float32",
            output_shape=output_shape,
            output_dtype="float32",
        )

    @property
    def supports_batch(self) -> bool:
        return True

    def predict(self, tensor: np.ndarray) -> np.ndarray:
        preds = self.model(tensor, training=False)
        return np.asarray(preds[0], dtype=np.float32)

    def predict_batch(self, batch: np.ndarray) -> np.ndarray:
        """Native batch inference — single forward pass for N faces."""
        preds = self.model(batch, training=False)
        return np.asarray(preds, dtype=np.float32)

    def details(self) -> InferenceDetails:
        return self._details


class TFLiteInferenceBackend(InferenceBackend):
    def __init__(self, model_path: str, num_threads: int = 1):
        self.model_path = model_path
        threads = max(1, int(num_threads))
        self.interpreter = tf.lite.Interpreter(model_path=model_path, num_threads=threads)
        self.interpreter.allocate_tensors()
        self.input_details = self.interpreter.get_input_details()[0]
        self.output_details = self.interpreter.get_output_details()[0]
        self.input_index = int(self.input_details["index"])
        self.output_index = int(self.output_details["index"])

        self._details = InferenceDetails(
            backend="tflite",
            model_path=model_path,
            input_shape=tuple(self.input_details.get("shape", [])),
            input_dtype=np.dtype(self.input_details.get("dtype", np.float32)).name,
            output_shape=tuple(self.output_details.get("shape", [])),
            output_dtype=np.dtype(self.output_details.get("dtype", np.float32)).name,
        )

    def predict(self, tensor: np.ndarray) -> np.ndarray:
        expected_dtype = self.input_details["dtype"]
        inp = np.asarray(tensor, dtype=expected_dtype)
        self.interpreter.set_tensor(self.input_index, inp)
        self.interpreter.invoke()
        output = self.interpreter.get_tensor(self.output_index)
        return np.asarray(output[0], dtype=np.float32)

    def details(self) -> InferenceDetails:
        return self._details


def create_inference_backend(
    backend: str,
    keras_model_path: str,
    tflite_model_path: str | None = None,
    tflite_num_threads: int = 1,
) -> InferenceBackend:
    backend_name = str(backend or "keras").strip().lower()
    if backend_name == "keras":
        return KerasInferenceBackend(keras_model_path)
    if backend_name == "tflite":
        if not tflite_model_path:
            raise ValueError("inference.tflite_model_path est requis quand backend=tflite")
        return TFLiteInferenceBackend(tflite_model_path, num_threads=tflite_num_threads)
    raise ValueError(f"Backend inférence non supporté: {backend}")
