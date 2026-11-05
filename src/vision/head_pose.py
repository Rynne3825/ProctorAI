from typing import Tuple, Optional, Any
import cv2
import mediapipe as mp
import numpy as np

from src.config import get_config


class HeadPoseEstimator:
    """
    Ước lượng tư thế và hướng quay đầu bằng MediaPipe Face Mesh & OpenCV solvePnP.
    """

    # 6 điểm mốc chuẩn trên khuôn mặt:
    # 1: Đỉnh mũi, 199: Đáy cằm, 33: Đuôi mắt trái, 263: Đuôi mắt phải, 61: Khóe miệng trái, 291: Khóe miệng phải
    FACE_KEYPOINTS = [1, 199, 33, 263, 61, 291]

    def __init__(self, cam_w: int = 640, cam_h: int = 480):
        self.cam_w = cam_w
        self.cam_h = cam_h
        self.cfg = get_config()

        # Ma trận camera giả định (Intrinsic Matrix)
        self.cam_matrix = np.array(
            [[cam_w, 0, cam_w / 2],
             [0, cam_w, cam_h / 2],
             [0, 0, 1]],
            dtype=np.float64
        )
        self.dist_coeffs = np.zeros((4, 1), dtype=np.float64)

        # Mô hình 3D chuẩn khuôn mặt (mm)
        self.model_points_3d = np.array([
            (0.0, 0.0, 0.0),             # Đỉnh mũi
            (0.0, -330.0, -65.0),        # Đáy cằm
            (-225.0, 170.0, -135.0),     # Mắt trái
            (225.0, 170.0, -135.0),      # Mắt phải
            (-150.0, -150.0, -125.0),    # Khóe miệng trái
            (150.0, -150.0, -125.0)      # Khóe miệng phải
        ], dtype=np.float64)

        # MediaPipe Face Mesh (refine_landmarks=False giúp tiết kiệm CPU)
        self.face_mesh = mp.solutions.face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=False,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

    def process(self, frame_bgr: np.ndarray) -> Tuple[int, int, Optional[str]]:
        """
        Phân tích frame hình ảnh và trả về:
        (pitch, yaw, violation_type)
        """
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(frame_rgb)

        if not results.multi_face_landmarks:
            return 0, 0, "Mất mặt / Che camera"

        landmarks = results.multi_face_landmarks[0].landmark

        # Trích xuất tọa độ 2D của 6 điểm mốc
        pts_2d = np.array([
            [landmarks[idx].x * self.cam_w, landmarks[idx].y * self.cam_h]
            for idx in self.FACE_KEYPOINTS
        ], dtype=np.float64)

        # Tọa độ 3D kết hợp chiều sâu Z từ MediaPipe
        pts_3d = np.array([
            [landmarks[idx].x * self.cam_w, landmarks[idx].y * self.cam_h, landmarks[idx].z * self.cam_w]
            for idx in self.FACE_KEYPOINTS
        ], dtype=np.float64)

        # Giải bài toán PnP
        success, rot_vec, _ = cv2.solvePnP(pts_3d, pts_2d, self.cam_matrix, self.dist_coeffs)
        if not success:
            return 0, 0, None

        rot_mat, _ = cv2.Rodrigues(rot_vec)
        angles, _, _, _, _, _ = cv2.RQDecomp3x3(rot_mat)

        pitch = int(angles[0] * 360)
        yaw = int(angles[1] * 360)

        # Đánh giá vi phạm theo ngưỡng cấu hình
        rules = self.cfg.head_pose
        violation = None

        if abs(yaw) > rules.yaw_backward_threshold:
            violation = "Quay hẳn ra sau"
        elif yaw > rules.yaw_side_threshold:
            violation = "Quay sang trái"
        elif yaw < -rules.yaw_side_threshold:
            violation = "Quay sang phải"
        elif pitch > rules.pitch_threshold:
            violation = "Ngửa mặt lên"
        elif pitch < -rules.pitch_threshold:
            violation = "Cúi xuống"

        return pitch, yaw, violation

    def close(self):
        self.face_mesh.close()
