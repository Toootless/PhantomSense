# Models - TinyML Activity Recognition

This directory contains pre-trained TinyML models for activity classification on the ESP32-S3.

## Models
- `activity_cnn.tflite` - CNN model for walking, sitting, falling detection
- `gesture_lstm.tflite` - LSTM model for hand gesture recognition (future)

## Training Pipeline
Models are trained using Python scripts in `training/` subdirectory:
- Data preprocessing and augmentation
- Model architecture definition
- Quantization for TensorFlow Lite
- Conversion to ESP32-S3 compatible format

## Model Specifications
- **Input:** 125 CSI samples × 48 subcarriers (preprocessed features)
- **Output:** 3 classes (Walking, Sitting, Falling)
- **Model Size:** ~50KB (quantized int8)
- **Inference Latency:** ~15ms on ESP32-S3

## Integration
Models are converted to C header files via `xxd` for embedding in firmware.

## References
- TensorFlow Lite for Microcontrollers
- ESP-NN optimized library for vector operations
