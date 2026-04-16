from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import tensorflow as tf


@dataclass
class InferenceDetails:
    backend: str
    device: str
    model_path: str
    input_shape: Any
    input_dtype: str
    output_shape: Any
    output_dtype: str


class InferenceBackend:
    @property
    def supports_batch(self) -> bool:
        return False

    def predict(self, tensor: np.ndarray) -> np.ndarray:
        raise NotImplementedError

    def predict_batch(self, batch: np.ndarray) -> np.ndarray:
        """Predict on a batch of N samples (N, H, W, C) → (N, num_classes)."""
        n = batch.shape[0]
        results = [self.predict(batch[i : i + 1]) for i in range(n)]
        return np.stack(results, axis=0)

    def gradcam(self, tensor: np.ndarray, class_idx: int | None = None) -> np.ndarray | None:
        return None

    def details(self) -> InferenceDetails:
        raise NotImplementedError

    def warmup(self, input_shape: tuple[int, ...], runs: int) -> None:
        runs = max(0, int(runs))
        if runs == 0:
            return
        dummy = np.zeros(input_shape, dtype=np.float32)
        for _ in range(runs):
            self.predict(dummy)


class KerasInferenceBackend(InferenceBackend):
    def __init__(self, model_path: str) -> None:
        self.model_path = model_path

        # Pick GPU if available, fall back to CPU
        gpus = tf.config.list_physical_devices("GPU")
        self._device = "/GPU:0" if gpus else "/CPU:0"

        with tf.device(self._device):
            self.model = tf.keras.models.load_model(model_path, compile=False)

        self._grad_model = self._build_grad_model()

        input_shape  = tuple(self.model.input_shape)
        output_shape = tuple(self.model.output_shape)
        self._details = InferenceDetails(
            backend="keras",
            device=self._device,
            model_path=model_path,
            input_shape=input_shape,
            input_dtype="float32",
            output_shape=output_shape,
            output_dtype="float32",
        )

    def _build_grad_model(self):
        """Build a model that outputs [last_conv_output, predictions]."""
        try:
            conv_layer = None
            for layer in self.model.layers:
                if hasattr(layer, "layers"):
                    out = layer.output
                    if hasattr(out, "shape") and len(out.shape) == 4:
                        conv_layer = layer
            if conv_layer is None:
                return None
            inp = tf.keras.Input(shape=self.model.input_shape[1:])
            x = inp
            conv_output = None
            for layer in self.model.layers:
                x = layer(x)
                if layer is conv_layer:
                    conv_output = x
            if conv_output is None:
                return None
            return tf.keras.Model(inputs=inp, outputs=[conv_output, x])
        except Exception:
            return None

    @property
    def supports_batch(self) -> bool:
        return True

    def predict(self, tensor: np.ndarray) -> np.ndarray:
        with tf.device(self._device):
            preds = self.model(tensor, training=False)
        return np.asarray(preds[0], dtype=np.float32)

    def predict_batch(self, batch: np.ndarray) -> np.ndarray:
        with tf.device(self._device):
            preds = self.model(batch, training=False)
        return np.asarray(preds, dtype=np.float32)

    def gradcam(self, tensor: np.ndarray, class_idx: int | None = None) -> np.ndarray | None:
        """Grad-CAM heatmap (H, W) float32 [0, 1] for the given input (1, H, W, C)."""
        if self._grad_model is None:
            return None

        with tf.device(self._device):
            inp = tf.cast(tensor, tf.float32)
            with tf.GradientTape() as tape:
                conv_out, preds = self._grad_model(inp, training=False)
                if class_idx is None:
                    class_idx = int(tf.argmax(preds[0]))
                loss = preds[:, class_idx]
            grads = tape.gradient(loss, conv_out)
        if grads is None:
            return None
        weights = tf.reduce_mean(grads, axis=(1, 2), keepdims=True)
        cam = tf.reduce_sum(conv_out * weights, axis=-1)[0]
        cam = tf.nn.relu(cam)
        cam_max = tf.reduce_max(cam)
        if cam_max > 0:
            cam = cam / cam_max
        return cam.numpy().astype(np.float32)

    def details(self) -> InferenceDetails:
        return self._details


class TFLiteInferenceBackend(InferenceBackend):
    """CPU-only TFLite backend — lightweight fallback when no GPU is available."""

    def __init__(self, model_path: str, num_threads: int = 1) -> None:
        self.model_path = model_path
        threads = max(1, int(num_threads))
        self.interpreter = tf.lite.Interpreter(
            model_path=model_path, num_threads=threads
        )
        self.interpreter.allocate_tensors()
        self.input_details  = self.interpreter.get_input_details()[0]
        self.output_details = self.interpreter.get_output_details()[0]
        self.input_index    = int(self.input_details["index"])
        self.output_index   = int(self.output_details["index"])

        self._details = InferenceDetails(
            backend="tflite",
            device="/CPU:0",
            model_path=model_path,
            input_shape=tuple(self.input_details.get("shape", [])),
            input_dtype=np.dtype(self.input_details.get("dtype", np.float32)).name,
            output_shape=tuple(self.output_details.get("shape", [])),
            output_dtype=np.dtype(self.output_details.get("dtype", np.float32)).name,
        )

    def predict(self, tensor: np.ndarray) -> np.ndarray:
        inp = np.asarray(tensor, dtype=self.input_details["dtype"])
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
    """
    Crée le backend d'inférence approprié.

    backend="auto"   → keras si GPU disponible, tflite sinon
    backend="keras"  → Keras/TF (GPU si disponible, sinon CPU)
    backend="tflite" → TFLite CPU uniquement (plus léger sans GPU)
    """
    name = str(backend or "auto").strip().lower()

    if name == "auto":
        gpus = tf.config.list_physical_devices("GPU")
        name = "keras" if gpus else "tflite"
        device_label = "GPU" if gpus else "CPU"
        print(f"[Backend] Auto-sélection → {name.upper()} ({device_label})")

    if name == "keras":
        return KerasInferenceBackend(keras_model_path)

    if name == "tflite":
        if not tflite_model_path:
            raise ValueError(
                "inference.tflite_model_path est requis quand backend=tflite"
            )
        return TFLiteInferenceBackend(tflite_model_path, num_threads=tflite_num_threads)

    raise ValueError(f"Backend inférence non supporté : '{backend}'")
