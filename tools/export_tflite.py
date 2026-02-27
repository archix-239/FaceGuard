#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import tensorflow as tf


def parse_args():
    parser = argparse.ArgumentParser(description="Export a Keras model to TFLite")
    parser.add_argument("--in", dest="input_model", required=True, help="Input .keras model path")
    parser.add_argument("--out", dest="output_model", required=True, help="Output .tflite path")
    return parser.parse_args()


def main():
    args = parse_args()
    input_path = Path(args.input_model)
    output_path = Path(args.output_model)

    if not input_path.exists():
        raise SystemExit(f"❌ Modèle introuvable: {input_path}")

    print(f"[⏳] Chargement du modèle Keras: {input_path}")
    model = tf.keras.models.load_model(str(input_path), compile=False)

    print("[⏳] Conversion en TFLite FP32...")
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    converter.optimizations = []
    tflite_model = converter.convert()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(tflite_model)
    size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"[✅] TFLite exporté: {output_path} ({size_mb:.2f} MB)")


if __name__ == "__main__":
    main()
