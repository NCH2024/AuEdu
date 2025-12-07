import numpy as np
import cv2
import onnxruntime as ort
import os

class LivenessAntiSpoof:
    """
    Liveness/Spoof detection using ONNX model.
    - Input: Face image BGR (numpy array)
    - Output: dict { 'label': 0 (live) or 1 (spoof), 'score': probability }
    """

    def __init__(self, model_path, device='cpu', model_img_size=128):
        # Try CUDA, fallback to CPU
        providers = ["CPUExecutionProvider"]
        if 'cuda' in device.lower():
            try:
                if ort.get_device() == 'GPU':
                    providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
            except Exception:
                pass
        self.session = ort.InferenceSession(model_path, providers=providers)
        self.input_name = self.session.get_inputs()[0].name
        self.model_img_size = model_img_size

    def _preprocess(self, img_bgr):
        """
        Resize + pad keeping aspect ratio, transpose, normalize to [0,1], batch dim.
        """
        if img_bgr is None or img_bgr.size == 0:
            return None
        new_size = self.model_img_size
        old_size = img_bgr.shape[:2]  # (h, w)
        ratio = float(new_size) / max(old_size)
        scaled_shape = tuple([int(x * ratio) for x in old_size])
        img = cv2.resize(img_bgr, (scaled_shape[1], scaled_shape[0]))
        delta_w = new_size - scaled_shape[1]
        delta_h = new_size - scaled_shape[0]
        top, bottom = delta_h // 2, delta_h - (delta_h // 2)
        left, right = delta_w // 2, delta_w - (delta_w // 2)
        img = cv2.copyMakeBorder(img, top, bottom, left, right, cv2.BORDER_CONSTANT, value=[0, 0, 0])
        img = img.transpose(2, 0, 1).astype(np.float32) / 255.0
        img = np.expand_dims(img, axis=0)
        return img

    def _softmax(self, x):
        x = np.array(x)
        x = x - np.max(x)
        e_x = np.exp(x)
        return e_x / np.sum(e_x)

    def predict(self, face_bgr):
        """
        Predict live/spoof.
        Returns dict: { 'label': 0 (live) or 1 (spoof), 'score': float }
        """
        x = self._preprocess(face_bgr)
        if x is None:
            return None
        ort_inputs = {self.input_name: x}
        logits = self.session.run(None, ort_inputs)[0]  # shape (1,2)
        logits = logits.ravel()
        probs = self._softmax(logits)
        # CelebA-Spoof: label 0 = live, 1 = spoof
        label = int(np.argmax(probs))
        score = float(probs[label])
        return {'label': label, 'score': score}

    def predict_label(self, face_bgr):
        """
        Trả về nhãn 0 (live) hoặc 1 (spoof), phù hợp dùng cho các hệ thống nhị phân.
        """
        result = self.predict(face_bgr)
        if result is not None:
            return float(result['label'])
        return None