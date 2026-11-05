import os
from typing import List, Tuple, Optional
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from src.config import get_config


class HUDRenderer:
    """Vẽ lớp phủ giao diện tiếng Việt (HUD Overlay) và quản lý màn hình Standby."""

    def __init__(self):
        self.cfg = get_config()
        font_path = self.cfg.paths.font_path

        if not os.path.exists(font_path):
            for f in ["C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/segoeui.ttf"]:
                if os.path.exists(f):
                    font_path = f
                    break

        try:
            self.font_title = ImageFont.truetype(font_path, 20)
            self.font_sub = ImageFont.truetype(font_path, 15)
            self.font_box = ImageFont.truetype(font_path, 13)
            self.font_standby = ImageFont.truetype(font_path, 22)
            self.font_standby_sub = ImageFont.truetype(font_path, 14)
        except Exception:
            self.font_title = self.font_sub = self.font_box = self.font_standby = self.font_standby_sub = ImageFont.load_default()

        # Cache màn hình Standby JPEG tạo sẵn để tiết kiệm 100% CPU khi hệ thống TẮT
        self._cached_standby_jpeg: Optional[bytes] = None

    def draw_hud(
        self,
        frame_rgb: np.ndarray,
        status_text: str,
        status_color_bgr: Tuple[int, int, int],
        angle_text: str,
        bboxes: List[Tuple[List[int], str, Tuple[int, int, int]]]
    ) -> np.ndarray:
        """Vẽ toàn bộ thông tin trạng thái, góc đầu và hộp bounding box lên video."""
        h, w = frame_rgb.shape[:2]

        # 1. Vẽ Bounding Box trên RGB
        for (x1, y1, x2, y2), _, bgr_color in bboxes:
            rgb_color = (bgr_color[2], bgr_color[1], bgr_color[0])
            cv2.rectangle(frame_rgb, (x1, y1), (x2, y2), rgb_color, 2)

        # 2. Vẽ chữ tiếng Việt bằng PIL
        img_pil = Image.fromarray(frame_rgb)
        draw = ImageDraw.Draw(img_pil)

        # Thanh trạng thái tối phía trên
        draw.rectangle([(0, 0), (w, 54)], fill=(15, 23, 42, 220))
        status_rgb = (status_color_bgr[2], status_color_bgr[1], status_color_bgr[0])

        draw.text((16, 8), status_text, font=self.font_title, fill=status_rgb)
        draw.text((16, 32), angle_text, font=self.font_sub, fill=(203, 213, 225))

        # Nhãn vật thể
        for (x1, y1, _, _), label, bgr_color in bboxes:
            tag_rgb = (bgr_color[2], bgr_color[1], bgr_color[0])
            box_y = max(56, y1 - 20)
            draw.rectangle([(x1, box_y), (x1 + len(label) * 8 + 14, box_y + 18)], fill=tag_rgb)
            draw.text((x1 + 6, box_y + 2), label, font=self.font_box, fill=(255, 255, 255))

        return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)

    def get_standby_jpeg(self, width: int = 640, height: int = 480) -> bytes:
        """Trả về frame Standby đã được pre-render sẵn trong bộ nhớ (0% CPU)."""
        if self._cached_standby_jpeg is not None:
            return self._cached_standby_jpeg

        standby_img = np.zeros((height, width, 3), dtype=np.uint8)
        standby_img[:] = (20, 15, 11)

        img_pil = Image.fromarray(cv2.cvtColor(standby_img, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(img_pil)

        cx, cy = width // 2, height // 2 - 30
        r = 45
        draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], fill=(30, 41, 59), outline=(71, 85, 105), width=2)
        draw.line([(cx - 20, cy + 20), (cx + 20, cy - 20)], fill=(239, 68, 68), width=3)

        draw.text((cx - 100, cy + 65), "HỆ THỐNG ĐANG TẮT", font=self.font_standby, fill=(241, 245, 249))
        draw.text((cx - 165, cy + 100), "Nhấn nút 'BẬT HỆ THỐNG' trên giao diện để bắt đầu", font=self.font_standby_sub, fill=(148, 163, 184))

        frame_bgr = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
        _, buffer = cv2.imencode(".jpg", frame_bgr, [cv2.IMWRITE_JPEG_QUALITY, 80])
        self._cached_standby_jpeg = buffer.tobytes()
        return self._cached_standby_jpeg
