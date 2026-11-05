import os
import csv
import uuid
from datetime import datetime
import cv2
import numpy as np

from src.config import get_config
from src.core.state import state_manager


def save_violation_snapshot(violation_type: str, duration: float, frame: np.ndarray) -> str:
    """
    Lưu ảnh bằng chứng vi phạm và ghi dòng nhật ký CSV chuẩn utf-8-sig.
    """
    cfg = get_config()
    now_dt = datetime.now()
    time_str = now_dt.strftime("%Y%m%d_%H%M%S")
    uid = uuid.uuid4().hex[:6]
    file_name = f"violation_{time_str}_{uid}.jpg"

    # 1. Lưu ảnh chụp bằng chứng vào thư mục screenshots/
    abs_img_path = os.path.join(cfg.paths.screenshots_dir, file_name)
    cv2.imwrite(abs_img_path, frame)

    # 2. Ghi nhật ký CSV (gom theo ngày, encoding utf-8-sig để Excel mở ra 100% chuẩn font)
    csv_file = os.path.join(cfg.paths.logs_dir, f"violations_{now_dt.strftime('%Y%m%d')}.csv")
    file_exists = os.path.exists(csv_file)
    with open(csv_file, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Thời gian", "Loại vi phạm", "Thời gian kéo dài (giây)", "File ảnh"])
        writer.writerow([
            now_dt.strftime("%Y-%m-%d %H:%M:%S"),
            violation_type,
            f"{duration:.2f}",
            file_name
        ])

    # 3. Cập nhật vào State Manager
    state_manager.record_violation(violation_type, duration, file_name)
    print(f"📸 [BẰNG CHỨNG] {now_dt.strftime('%H:%M:%S')} - {violation_type} ({duration:.2f}s) -> {file_name}")

    return file_name
