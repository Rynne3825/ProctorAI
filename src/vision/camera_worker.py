import time
import threading
from typing import Optional, List, Tuple
import cv2
import numpy as np

from src.config import get_config
from src.core.state import state_manager
from src.core.logger import save_violation_snapshot
from src.vision.head_pose import HeadPoseEstimator
from src.vision.yolo_detector import YoloDetector
from src.vision.hud_renderer import HUDRenderer


class CameraWorker(threading.Thread):
    """
    Luồng nền độc lập điều phối việc đọc Camera, điều phối nhận diện AI và tạo buffer phát sóng MJPEG.
    Hỗ trợ Master Switch: Tự động ngắt camera phần cứng và hạ CPU về 0% khi TẮT.
    """

    def __init__(self):
        super().__init__(daemon=True)
        self.cfg = get_config()
        self.running: bool = True
        self._lock = threading.Lock()
        self.latest_jpeg: Optional[bytes] = None

        # Khởi tạo các module thị giác
        self.hud_renderer = HUDRenderer()
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
            print(f"✅ Camera đã mở thành công (Thiết bị {self.cfg.camera.device_id})")
        else:
            print(f"⚠️ Chưa thể mở webcam {self.cfg.camera.device_id}. Hệ thống sẽ thử lại...")

    def _release_camera(self):
        """Giải phóng camera phần cứng khi TẮT hệ thống nhằm bảo mật tối đa."""
        if self.cap is not None and self.cap.isOpened():
            self.cap.release()
            self.cap = None
            print("🔒 Đã giải phóng Camera phần cứng (Chế độ Bảo Mật Standby)")

    def run(self):
        frame_count = 0
        violation_start: Optional[float] = None
        current_violation: Optional[str] = None
        has_snapped_current = False
        last_warning_time = 0.0

        cached_yolo_violation: Optional[str] = None
        cached_yolo_bboxes: List[Tuple[List[int], str, Tuple[int, int, int]]] = []

        rules = self.cfg.rules

        while self.running:
            is_active = state_manager.is_active()

            # ================= 1. TRẠNG THÁI HỆ THỐNG ĐANG TẮT (STANDBY) =================
            if not is_active:
                self._release_camera()
                standby_frame = self.hud_renderer.draw_standby(self.cfg.camera.width, self.cfg.camera.height)
                _, buffer = cv2.imencode(".jpg", standby_frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                with self._lock:
                    self.latest_jpeg = buffer.tobytes()

                # Reset các biến đo đạc vi phạm
                violation_start = None
                current_violation = None
                has_snapped_current = False
                cached_yolo_violation = None
                cached_yolo_bboxes = []

                time.sleep(0.1)  # Giảm tải CPU về 0% khi tắt
                continue

            # ================= 2. TRẠNG THÁI HỆ THỐNG ĐANG BẬT (ACTIVE) =================
            if self.cap is None or not self.cap.isOpened():
                self._init_camera()
                time.sleep(0.05)
                continue

            ret, frame = self.cap.read()
            if not ret or frame is None:
                time.sleep(0.03)
                continue

            # Lật ảnh gương để trải nghiệm tự nhiên
            frame = cv2.flip(frame, 1)
            frame_count += 1
            now = time.time()

            # A. Quét YOLO phát hiện thiết bị (áp dụng Frame Skip để tối ưu tài nguyên)
            if frame_count % self.cfg.yolo.frame_skip == 0:
                cached_yolo_violation, cached_yolo_bboxes = self.yolo.detect(frame)

            # B. Quét MediaPipe Face Mesh ước lượng hướng đầu
            pitch, yaw, pose_violation = self.head_pose.process(frame)

            # C. Xác định hành vi vi phạm hiện thời (Ưu tiên thiết bị cấm > tư thế đầu)
            active_violation = cached_yolo_violation or pose_violation

            if active_violation != current_violation:
                violation_start = now if active_violation else None
                current_violation = active_violation
                has_snapped_current = False

            duration = (now - violation_start) if violation_start else 0.0
            thresh = rules.no_face_threshold_seconds if active_violation == "Mất mặt / Che camera" else rules.violation_threshold_seconds

            is_warning = duration > thresh

            # D. Tự động chụp và lưu bằng chứng khi vượt ngưỡng
            if is_warning and not has_snapped_current:
                save_violation_snapshot(active_violation, duration, frame)
                has_snapped_current = True
                last_warning_time = now
            elif is_warning and (now - last_warning_time > rules.snap_interval_extended_seconds):
                # Vi phạm tiếp tục kéo dài -> chụp thêm 1 ảnh sau mỗi khoảng thời gian cấu hình
                save_violation_snapshot(active_violation, duration, frame)
                last_warning_time = now

            # E. Xác định thông điệp & màu sắc hiển thị lên HUD
            if is_warning:
                status_text = f"CẢNH BÁO VI PHẠM: {active_violation} ({duration:.1f}s)"
                status_color = (0, 0, 255)  # Đỏ rực
            elif active_violation:
                status_text = f"Đang chú ý: {active_violation} ({duration:.1f}s)"
                status_color = (0, 255, 255)  # Vàng
            else:
                status_text = "BÌNH THƯỜNG - HỢP LỆ"
                status_color = (0, 255, 0)  # Xanh lục

            angle_text = f"Góc nhìn: Pitch: {pitch}° | Yaw: {yaw}°"

            # F. Vẽ lớp phủ HUD
            frame_annotated = self.hud_renderer.draw_hud(
                frame, status_text, status_color, angle_text, cached_yolo_bboxes
            )

            # G. Nén thành JPEG đưa vào buffer cho Web Streamer
            _, buffer = cv2.imencode(".jpg", frame_annotated, [cv2.IMWRITE_JPEG_QUALITY, 85])
            with self._lock:
                self.latest_jpeg = buffer.tobytes()

            time.sleep(1.0 / self.cfg.camera.fps_limit)

    def get_jpeg(self) -> Optional[bytes]:
        """Lấy frame JPEG mới nhất an toàn."""
        with self._lock:
            return self.latest_jpeg

    def stop(self):
        """Dừng worker khi đóng ứng dụng."""
        self.running = False
        self._release_camera()
        self.head_pose.close()
