import os
from typing import List, Tuple
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from src.config import get_config


class HUDRenderer:
    """
    Vẽ lớp phủ giao diện tiếng Việt (HUD Overlay) sắc nét, chống nhòe font và hiển thị bounding box chuyên nghiệp.
    """

    def __init__(self):
        self.cfg = get_config()
        font_path = self.cfg.paths.font_path

        # Tự động tìm font TrueType tiếng Việt trên hệ thống Windows
        if not os.path.exists(font_path):
            fallbacks = [
                "C:/Windows/Fonts/arialbd.ttf",
                "C:/Windows/Fonts/arial.ttf",
                "C:/Windows/Fonts/segoeui.ttf",
                "C:/Windows/Fonts/tahoma.ttf"
            ]
            for f in fallbacks:
                if os.path.exists(f):
                    font_path = f
                    break

        try:
            self.font_title = ImageFont.truetype(font_path, 20)
            self.font_sub = ImageFont.truetype(font_path, 15)
            self.font_box = ImageFont.truetype(font_path, 13)
            self.font_standby_title = ImageFont.truetype(font_path, 22)
            self.font_standby_sub = ImageFont.truetype(font_path, 14)
        except Exception:
            self.font_title = ImageFont.load_default()
            self.font_sub = ImageFont.load_default()
            self.font_box = ImageFont.load_default()
            self.font_standby_title = ImageFont.load_default()
            self.font_standby_sub = ImageFont.load_default()

    def draw_hud(
        self,
        frame: np.ndarray,
        status_text: str,
        status_color_bgr: Tuple[int, int, int],
        angle_text: str,
        bboxes: List[Tuple[List[int], str, Tuple[int, int, int]]]
    ) -> np.ndarray:
        """Vẽ toàn bộ thông tin trạng thái, góc đầu và hộp bounding box lên video."""
        h, w = frame.shape[:2]

        # 1. Vẽ Bounding Box vật thể bằng OpenCV
        for (x1, y1, x2, y2), _, bgr_color in bboxes:
            cv2.rectangle(frame, (x1, y1), (x2, y2), bgr_color, 2)

        # 2. Chuyển sang PIL để vẽ chữ tiếng Việt có dấu sắc nét
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(frame_rgb)
        draw = ImageDraw.Draw(img_pil)

        # 3. Vẽ dải nền tối trên đỉnh (Top Status Bar)
        draw.rectangle([(0, 0), (w, 54)], fill=(15, 23, 42, 220))

        # Đổi BGR sang RGB cho PIL
        status_rgb = (status_color_bgr[2], status_color_bgr[1], status_color_bgr[0])

        # Vẽ trạng thái chính (CẢNH BÁO / CHÚ Ý / BÌNH THƯỜNG)
        draw.text((16, 8), status_text, font=self.font_title, fill=status_rgb)

        # Vẽ góc Euler (Pitch, Yaw)
        draw.text((16, 32), angle_text, font=self.font_sub, fill=(203, 213, 225))

        # 4. Vẽ nhãn cho từng Bounding Box
        for (x1, y1, _, _), label, bgr_color in bboxes:
            tag_rgb = (bgr_color[2], bgr_color[1], bgr_color[0])
            # Hộp nền cho nhãn
            box_y = max(56, y1 - 20)
            draw.rectangle([(x1, box_y), (x1 + len(label) * 8 + 14, box_y + 18)], fill=tag_rgb)
            draw.text((x1 + 6, box_y + 2), label, font=self.font_box, fill=(255, 255, 255))

        return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)

    def draw_standby(self, width: int = 640, height: int = 480) -> np.ndarray:
        """Tạo khung hình Standby hiện đại khi Master Switch ở trạng thái TẮT."""
        # Nền gradient slate tối
        standby_img = np.zeros((height, width, 3), dtype=np.uint8)
        standby_img[:] = (20, 15, 11)  # BGR Dark Navy / Slate

        img_pil = Image.fromarray(cv2.cvtColor(standby_img, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(img_pil)

        # Vẽ vòng tròn trung tâm
        cx, cy = width // 2, height // 2 - 30
        r = 45
        draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], fill=(30, 41, 59), outline=(71, 85, 105), width=2)
        draw.line([(cx - 20, cy + 20), (cx + 20, cy - 20)], fill=(239, 68, 68), width=3)

        # Thông báo trạng thái
        text_title = "HỆ THỐNG ĐANG TẮT"
        draw.text((cx - 100, cy + 65), text_title, font=self.font_standby_title, fill=(241, 245, 249))

        text_sub = "Nhấn nút 'BẬT HỆ THỐNG' trên giao diện để bắt đầu"
        draw.text((cx - 165, cy + 100), text_sub, font=self.font_standby_sub, fill=(148, 163, 184))

        return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
