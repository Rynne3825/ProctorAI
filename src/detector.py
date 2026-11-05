import os
from typing import Tuple, List, Optional
import numpy as np
from ultralytics import YOLO

from src.config import get_config


class YoloDetector:
    """Bộ nhận diện thiết bị linh hoạt (YOLO11) với cấu hình mở rộng qua config.yaml."""

    def __init__(self, model_path: Optional[str] = None):
        self.cfg = get_config()
        self.model_path = model_path or self.cfg.yolo.model_path

        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Không tìm thấy mô hình YOLO tại: {self.model_path}")

        self.model = YOLO(self.model_path)

    def detect(self, frame: np.ndarray) -> Tuple[Optional[str], List[Tuple[List[int], str, Tuple[int, int, int]]]]:
        """Quét các vật thể trong khung hình và trả về (violation_text, bboxes)."""
        violation: Optional[str] = None
        bboxes: List[Tuple[List[int], str, Tuple[int, int, int]]] = []

        results = self.model(frame, verbose=False)
        device_rules = self.cfg.yolo.device_rules or {}

        for r in results:
            for box in r.boxes:
                conf = float(box.conf[0])
                if conf < self.cfg.yolo.confidence_threshold:
                    continue

                cls_id = int(box.cls[0])
                raw_name = self.model.names[cls_id].lower()
                coords = list(map(int, box.xyxy[0]))

                # 1. Tra cứu theo quy tắc trong config.yaml
                matched_rule = None
                for key, rule in device_rules.items():
                    if key.lower() in raw_name:
                        matched_rule = rule
                        break

                if matched_rule:
                    label = f"{matched_rule.get('label', raw_name.upper())} ({conf:.0%})"
                    color = tuple(matched_rule.get('color', [0, 0, 255]))
                    is_violation = matched_rule.get('is_violation', True)
                    warning_text = matched_rule.get('warning_text', f"Phát hiện {label}")

                    if is_violation and violation is None:
                        violation = warning_text

                    bboxes.append((coords, label, color))
                else:
                    # 2. Xử lý dự phòng thông minh
                    if any(k in raw_name for k in ["phone", "cell", "mobile"]):
                        bboxes.append((coords, f"PHONE ({conf:.0%})", (0, 0, 255)))
                        if violation is None:
                            violation = "Sử dụng ĐIỆN THOẠI"
                    elif any(k in raw_name for k in ["calc", "calculator"]):
                        bboxes.append((coords, f"MÁY TÍNH ({conf:.0%})", (0, 255, 0)))
                    else:
                        bboxes.append((coords, f"{raw_name.upper()} ({conf:.0%})", (200, 200, 200)))

        return violation, bboxes
