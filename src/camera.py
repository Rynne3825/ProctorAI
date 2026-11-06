import time
import threading
from typing import Optional, List, Tuple
import cv2
import numpy as np

from src.config import get_config
from src.state import state_manager
from src.logger import save_violation_snapshot
from src.head_pose import HeadPoseEstimator
from src.detector import YoloDetector
from src.hud import HUDRenderer


class CameraWorker(threading.Thread):
    """Luồng nền độc lập điều phối việc đọc Camera, suy luận AI và tạo buffer MJPEG."""

    def __init__(self):
        super().__init__(daemon=True)
        self.cfg = get_config()
        self.running: bool = True
        self._lock = threading.Lock()
        self.latest_jpeg: Optional[bytes] = None

        self.hud = HUDRenderer()
        self.head_pose = HeadPoseEstimator(self.cfg.camera.width, self.cfg.camera.height)
        self.yolo = YoloDetector(self.cfg.yolo.model_path)

        self.cap: Optional[cv2.VideoCapture] = None
        self._init_camera()

    def _init_camera(self):
        """Khởi tạo kết nối tới Webcam thiết bị."""
        if self.cap is not None and self.cap.isOpened():
            return
        self.cap = cv2.VideoCapture(self.cfg.camera.device_id)
        if self.cap.isOpened():
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.cfg.camera.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.cfg.camera.height)

    def _release_camera(self):
        """Giải phóng camera phần cứng khi TẮT hệ thống nhằm bảo mật tối đa."""
        if self.cap is not None and self.cap.isOpened():
            self.cap.release()
            self.cap = None

    def run(self):
        frame_count = 0
        violation_start: Optional[float] = None
        current_group: Optional[str] = None
        current_violation: Optional[str] = None
        has_snapped_current = False
        last_warning_time = 0.0

        cached_yolo_violation: Optional[str] = None
        cached_yolo_bboxes: List[Tuple[List[int], str, Tuple[int, int, int]]] = []

        rules = self.cfg.rules

        while self.running:
            is_active = state_manager.is_active()

            # 1. STANDBY: Camera tắt, CPU 0%
            if not is_active:
                self._release_camera()
                standby_bytes = self.hud.get_standby_jpeg(self.cfg.camera.width, self.cfg.camera.height)
                with self._lock:
                    self.latest_jpeg = standby_bytes

                violation_start = None
                current_group = None
                current_violation = None
                has_snapped_current = False
                cached_yolo_violation = None
                cached_yolo_bboxes = []
                time.sleep(0.1)
                continue

            # 2. ACTIVE: Camera mở và chạy AI
            if self.cap is None or not self.cap.isOpened():
                self._init_camera()
                time.sleep(0.05)
                continue

            ret, frame = self.cap.read()
            if not ret or frame is None:
                time.sleep(0.03)
                continue

            frame = cv2.flip(frame, 1)
            frame_count += 1
            now = time.time()

            # Chuyển đổi màu RGB một lần duy nhất dùng cho cả FaceMesh và PIL HUD
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Quét YOLO (áp dụng Frame Skip)
            if frame_count % self.cfg.yolo.frame_skip == 0:
                cached_yolo_violation, cached_yolo_bboxes = self.yolo.detect(frame)

            # Quét MediaPipe Face Mesh (Đếm số người & hướng đầu)
            pitch, yaw, pose_violation = self.head_pose.process(frame_rgb)

            # Đánh giá vi phạm và phân nhóm (Ưu tiên: Có người thứ 2 > Thiết bị cấm > Che mặt / Hướng đầu)
            active_violation: Optional[str] = None
            active_group: Optional[str] = None

            if pose_violation and "người" in pose_violation.lower():
                active_violation = pose_violation
                active_group = "MULTIPLE_FACES"
            elif cached_yolo_violation:
                active_violation = cached_yolo_violation
                active_group = "DEVICE"
            elif pose_violation:
                active_violation = pose_violation
                active_group = "NO_FACE" if ("mất mặt" in pose_violation.lower() or "che camera" in pose_violation.lower()) else "HEAD_POSE"

            # Ổn định bộ đếm thời gian: Không reset timer khi chỉ đổi góc quay chi tiết trong cùng một nhóm
            if active_group != current_group:
                violation_start = now if active_group else None
                current_group = active_group
                current_violation = active_violation
                has_snapped_current = False
            else:
                current_violation = active_violation

            duration = (now - violation_start) if violation_start else 0.0

            # Đánh giá cảnh báo
            if active_group == "MULTIPLE_FACES":
                # Người thứ hai: vi phạm nghiêm trọng -> chụp bằng chứng ngay lập tức (0.0s)
                is_warning = True
            elif active_group == "NO_FACE":
                is_warning = duration > rules.no_face_threshold_seconds
            elif active_group in ("DEVICE", "HEAD_POSE"):
                is_warning = duration > rules.violation_threshold_seconds
            else:
                is_warning = False

            # Lưu bằng chứng vi phạm
            if is_warning and not has_snapped_current:
                save_violation_snapshot(current_violation or "Vi phạm", duration, frame)
                has_snapped_current = True
                last_warning_time = now
            elif is_warning and (now - last_warning_time > rules.snap_interval_extended_seconds):
                save_violation_snapshot(current_violation or "Vi phạm", duration, frame)
                last_warning_time = now

            # Thông điệp trạng thái HUD
            if is_warning:
                dur_text = " (TỨC THỜI)" if active_group == "MULTIPLE_FACES" else f" ({duration:.1f}s)"
                status_text, status_color = f"CẢNH BÁO VI PHẠM: {current_violation}{dur_text}", (0, 0, 255)
            elif active_violation:
                status_text, status_color = f"Đang chú ý: {current_violation} ({duration:.1f}s)", (0, 255, 255)
            else:
                status_text, status_color = "BÌNH THƯỜNG - HỢP LỆ", (0, 255, 0)

            angle_text = f"Góc nhìn: Pitch: {pitch}° | Yaw: {yaw}°"

            # Vẽ HUD và nén JPEG
            frame_annotated = self.hud.draw_hud(frame_rgb, status_text, status_color, angle_text, cached_yolo_bboxes)
            _, buffer = cv2.imencode(".jpg", frame_annotated, [cv2.IMWRITE_JPEG_QUALITY, 85])
            with self._lock:
                self.latest_jpeg = buffer.tobytes()

            time.sleep(1.0 / self.cfg.camera.fps_limit)

    def get_jpeg(self) -> Optional[bytes]:
        with self._lock:
            return self.latest_jpeg

    def stop(self):
        self.running = False
        self._release_camera()
        self.head_pose.close()
