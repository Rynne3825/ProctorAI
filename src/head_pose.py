from typing import Tuple, Optional
import cv2
import mediapipe as mp
import numpy as np

from src.config import get_config


class HeadPoseEstimator:
    """
    Ước lượng tư thế đầu (MediaPipe Face Mesh + solvePnP) 
    và đếm số lượng khuôn mặt (Phát hiện người thứ hai trong phòng thi).
    """

    # 6 điểm mốc chuẩn trên khuôn mặt (MediaPipe Face Mesh index)
    FACE_KEYPOINTS = [1, 199, 33, 263, 61, 291]

    # Mô hình 3D chuẩn khuôn mặt nhân trắc học (Anthropometric 3D Face Model - mm)
    # Gốc (0, 0, 0) tại đỉnh mũi.
    # X: Trục ngang (Trái âm, Phải dương).
    # Y: Trục dọc (Trên âm, Dưới dương theo chiều pixel ảnh).
    # Z: Trục sâu (Hướng vào trong đầu, lùi xa camera).
    MODEL_POINTS_3D = np.array([
        (0.0, 0.0, 0.0),             # 1: Đỉnh mũi
        (0.0, 110.0, 65.0),          # 199: Đáy cằm
        (-65.0, -50.0, 60.0),        # 33: Khóe mắt trái
        (65.0, -50.0, 60.0),         # 263: Khóe mắt phải
        (-40.0, 50.0, 40.0),         # 61: Khóe miệng trái
        (40.0, 50.0, 40.0)           # 291: Khóe miệng phải
    ], dtype=np.float64)

    DIST_COEFFS = np.zeros((4, 1), dtype=np.float64)

    def __init__(self, cam_w: int = 640, cam_h: int = 480):
        self.cam_w = cam_w
        self.cam_h = cam_h
        self.cfg = get_config()

        self.cam_matrix = np.array(
            [[cam_w, 0, cam_w / 2],
             [0, cam_w, cam_h / 2],
             [0, 0, 1]],
            dtype=np.float64
        )

        # max_num_faces=4 để đếm chính xác số người trong khung hình
        self.face_mesh = mp.solutions.face_mesh.FaceMesh(
            max_num_faces=4,
            refine_landmarks=False,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

    def process(self, frame_rgb: np.ndarray) -> Tuple[float, float, Optional[str]]:
        """
        Phân tích ảnh RGB và trả về:
        (pitch, yaw, violation_type)
        """
        results = self.face_mesh.process(frame_rgb)

        if not results.multi_face_landmarks:
            return 0.0, 0.0, "Mất mặt / Che camera"

        num_faces = len(results.multi_face_landmarks)

        # CẢNH BÁO ĐẶC BIỆT: Phát hiện có người thứ 2 trở lên trong khung hình
        if num_faces > 1:
            return 0.0, 0.0, f"Phát hiện {num_faces} người (Có người thứ hai)"

        # Khi chỉ có đúng 1 thí sinh: Tính toán góc quay đầu solvePnP (SQPNP)
        landmarks = results.multi_face_landmarks[0].landmark

        pts_2d = np.array([
            [landmarks[idx].x * self.cam_w, landmarks[idx].y * self.cam_h]
            for idx in self.FACE_KEYPOINTS
        ], dtype=np.float64)

        success, rot_vec, _ = cv2.solvePnP(
            self.MODEL_POINTS_3D,
            pts_2d,
            self.cam_matrix,
            self.DIST_COEFFS,
            flags=cv2.SOLVEPNP_SQPNP
        )
        if not success:
            return 0.0, 0.0, None

        rot_mat, _ = cv2.Rodrigues(rot_vec)
        angles, _, _, _, _, _ = cv2.RQDecomp3x3(rot_mat)

        # RQDecomp3x3 đã trả về độ (°), làm tròn 1 chữ số thập phân
        pitch = round(float(angles[0]), 1)
        yaw = round(float(angles[1]), 1)

        rules = self.cfg.head_pose
        violation = None

        if abs(yaw) > rules.yaw_backward_threshold:
            violation = "Quay hẳn ra sau"
        elif yaw > rules.yaw_side_threshold:
            violation = "Quay sang trái"
        elif yaw < -rules.yaw_side_threshold:
            violation = "Quay sang phải"
        elif pitch > rules.pitch_threshold:
            violation = "Cúi xuống"
        elif pitch < -rules.pitch_threshold:
            violation = "Ngửa mặt lên"

        return pitch, yaw, violation

    def close(self):
        self.face_mesh.close()
